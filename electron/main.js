'use strict'

const { app, BrowserWindow, ipcMain, dialog, nativeTheme, shell } = require('electron')
const { spawn } = require('child_process')
const path   = require('path')
const fs     = require('fs')
const http   = require('http')

// ============================================================================
// Constants
// ============================================================================

const PORT     = 8765
const IS_DEV   = !app.isPackaged
const USER_DIR = app.getPath('userData')
const KEY_FILE = path.join(USER_DIR, 'api_key')
const LOG_FILE = path.join(USER_DIR, 'pitchcraft.log')

let backendProcess = null
let mainWindow     = null
let splashWindow   = null

// ============================================================================
// Logging
// ============================================================================

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`
  process.stdout.write(line)
  try { fs.appendFileSync(LOG_FILE, line) } catch {}
}

// ============================================================================
// Paths — dev uses project root, packaged uses process.resourcesPath
// ============================================================================

function resourcesPath() {
  return IS_DEV ? path.join(__dirname, '..') : process.resourcesPath
}

function pythonBin() {
  if (IS_DEV) {
    const devVenv = path.join(__dirname, '..', 'backend', '.venv', 'bin', 'python3')
    if (fs.existsSync(devVenv)) return devVenv
    return 'python3'
  }
  const venv = path.join(process.resourcesPath, 'venv')
  return process.platform === 'win32'
    ? path.join(venv, 'Scripts', 'python.exe')
    : path.join(venv, 'bin', 'python3')
}

function backendDir() {
  return path.join(resourcesPath(), 'backend')
}

// ============================================================================
// API Key — stored in Electron userData folder (never inside the .app)
// ============================================================================

function loadApiKey() {
  try {
    if (fs.existsSync(KEY_FILE)) return fs.readFileSync(KEY_FILE, 'utf8').trim() || null
  } catch {}
  return null
}

function saveApiKey(key) {
  fs.mkdirSync(USER_DIR, { recursive: true })
  fs.writeFileSync(KEY_FILE, key.trim(), { mode: 0o600 })
}

// ============================================================================
// Backend health check
// ============================================================================

function checkHealth() {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${PORT}/api/health`, (res) => {
      resolve(res.statusCode === 200)
    })
    req.on('error', () => resolve(false))
    req.setTimeout(2000, () => { req.destroy(); resolve(false) })
  })
}

async function waitForBackend(attempts = 60) {
  for (let i = 0; i < attempts; i++) {
    if (await checkHealth()) return true
    await new Promise(r => setTimeout(r, 1000))
  }
  return false
}

// ============================================================================
// Start Python backend
// ============================================================================

async function startBackend(apiKey) {
  const python  = pythonBin()
  const backend = backendDir()

  if (!fs.existsSync(python)) {
    throw new Error(
      `Bundled Python not found at:\n${python}\n\n` +
      `Run  ./build_app.sh  to rebuild the application.`
    )
  }

  log(`Backend: ${python}`)
  log(`Working dir: ${backend}`)

  const env = {
    ...process.env,
    OPENAI_API_KEY: apiKey,
    PATH: `${path.dirname(python)}:${process.env.PATH}`,
  }

  backendProcess = spawn(
    python,
    ['-m', 'uvicorn', 'main:app',
     '--host', '127.0.0.1',
     '--port', String(PORT),
     '--log-level', 'warning'],
    { cwd: backend, env, detached: false }
  )

  backendProcess.stdout?.on('data', d => log(`[py] ${d.toString().trim()}`))
  backendProcess.stderr?.on('data', d => log(`[py] ${d.toString().trim()}`))
  backendProcess.on('error',  err  => log(`[py error] ${err.message}`))
  backendProcess.on('exit',   code => log(`[py] exited ${code}`))

  return waitForBackend()
}

// ============================================================================
// Setup window (first-run API key)
// ============================================================================

function showSetup() {
  return new Promise((resolve) => {
    const win = new BrowserWindow({
      width:     500,
      height:    360,
      resizable: false,
      frame:     false,
      backgroundColor: '#0A0F1E',
      webPreferences: {
        preload:          path.join(__dirname, 'preload.js'),
        nodeIntegration:  false,
        contextIsolation: true,
      },
    })

    win.loadFile(path.join(__dirname, 'setup.html'))

    ipcMain.once('api-key-submit', (_, key) => {
      saveApiKey(key)
      win.close()
      resolve(key.trim())
    })

    ipcMain.once('api-key-cancel', () => {
      win.close()
      resolve(null)
    })

    win.on('closed', () => resolve(null))
  })
}

// ============================================================================
// Splash window
// ============================================================================

function createSplash() {
  splashWindow = new BrowserWindow({
    width:       400,
    height:      260,
    frame:       false,
    transparent: true,
    alwaysOnTop: true,
    resizable:   false,
    webPreferences: { nodeIntegration: false },
  })
  splashWindow.loadFile(path.join(__dirname, 'splash.html'))
}

function closeSplash() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close()
    splashWindow = null
  }
}

// ============================================================================
// Main window
// ============================================================================

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width:           1280,
    height:          820,
    minWidth:        900,
    minHeight:       600,
    titleBarStyle:   'hiddenInset',
    backgroundColor: '#0A0F1E',
    webPreferences: {
      nodeIntegration:  false,
      contextIsolation: true,
      preload:          path.join(__dirname, 'preload.js'),
    },
    show: false,
  })

  mainWindow.loadURL(`http://127.0.0.1:${PORT}`)

  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.show()
    mainWindow.focus()
  })

  // Open external links in the system browser, not in Electron
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => { mainWindow = null })
}

// ============================================================================
// IPC handlers
// ============================================================================

ipcMain.handle('reset-api-key', () => {
  try { fs.unlinkSync(KEY_FILE) } catch {}
  app.relaunch()
  app.exit()
})

ipcMain.handle('open-logs', () => {
  shell.openPath(LOG_FILE)
})

// ============================================================================
// App lifecycle
// ============================================================================

app.whenReady().then(async () => {
  nativeTheme.themeSource = 'dark'

  try {
    // Step 1: Ensure API key
    let apiKey = loadApiKey()
    if (!apiKey) {
      apiKey = await showSetup()
      if (!apiKey) { app.quit(); return }
    }

    // Step 2: Show splash while backend starts
    createSplash()
    log('Starting backend...')

    const ready = await startBackend(apiKey)
    closeSplash()

    if (!ready) {
      const choice = dialog.showMessageBoxSync({
        type:    'error',
        title:   'PitchCraft — Startup Error',
        message: 'The backend could not start.',
        detail:  `Check the log for details:\n${LOG_FILE}`,
        buttons: ['Open Log', 'Quit'],
      })
      if (choice === 0) shell.openPath(LOG_FILE)
      app.quit()
      return
    }

    log('Backend ready — opening main window')
    createMainWindow()

  } catch (err) {
    closeSplash()
    log(`Fatal: ${err.message}`)
    dialog.showErrorBox('PitchCraft — Fatal Error', err.message)
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  if (backendProcess && !backendProcess.killed) {
    log('Stopping backend...')
    backendProcess.kill('SIGTERM')
  }
})
