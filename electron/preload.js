'use strict'

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('pitchcraft', {
  submitApiKey: (key)  => ipcRenderer.send('api-key-submit', key),
  cancelSetup:  ()     => ipcRenderer.send('api-key-cancel'),
  resetApiKey:  ()     => ipcRenderer.invoke('reset-api-key'),
  openLogs:     ()     => ipcRenderer.invoke('open-logs'),
})
