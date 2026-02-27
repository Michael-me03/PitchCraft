// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useCallback, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { PanelLeft, MessageSquare, X } from "lucide-react";
import { TEMPLATES } from "../data/templates";
import type { Template } from "../types/template";
import type { ChatMessage, SessionSettings, PreviewData } from "../types/chat";
import { useChatSessions } from "../hooks/useChatSessions";
import { useGeneration } from "../hooks/useGeneration";
import HistorySidebar from "./HistorySidebar";
import WorkspacePanel from "./WorkspacePanel";
import ChatPanel from "./ChatPanel";
import SettingsPanel from "./SettingsPanel";

// ============================================================================
// SECTION: Constants
// ============================================================================

const CUSTOM_UPLOAD_TEMPLATE: Template = {
  id: "custom-upload",
  name: "Custom Template",
  category: "Business",
  description: "Your own uploaded .pptx template",
  tags: ["custom", "upload"],
  colors: { bg: "#1a1a2e", accent: "#6366f1", text: "#e2e8f0", muted: "#64748b" },
};

// ============================================================================
// SECTION: Helpers
// ============================================================================

function generateId(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function makeMessage(partial: Omit<ChatMessage, "id" | "timestamp">): ChatMessage {
  return { ...partial, id: generateId(), timestamp: Date.now() };
}

// ============================================================================
// SECTION: Component
// ============================================================================

export default function ChatLayout() {
  // ── Session state ──────────────────────────────────────────────────────
  const sessions = useChatSessions();
  const {
    activeSession,
    activeSessionId,
    setActiveSessionId,
    createSession,
    addMessage,
    updateSession,
    updateSettings,
    deleteSession,
  } = sessions;

  // ── Generation state ───────────────────────────────────────────────────
  const { phase, previewData, setPreviewData, generate, iterate, clarify, cancel } =
    useGeneration(
      addMessage,
      activeSessionId,
      updateSession as (sid: string, u: Record<string, unknown>) => void,
    );

  // ── UI state ───────────────────────────────────────────────────────────
  const [historyOpen, setHistoryOpen] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    TEMPLATES[0] ?? null,
  );
  const [customTemplateFile, setCustomTemplateFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pendingClarify, setPendingClarify] = useState(false);
  const [clarifyParams, setClarifyParams] = useState<Record<string, string>>({});
  const [showSetup, setShowSetup] = useState(true);
  const prevPreviewRef = useRef<PreviewData | null>(null);

  // ── Sync template from session settings ────────────────────────────────
  useEffect(() => {
    if (activeSession?.settings.templateId) {
      const found = TEMPLATES.find((t) => t.id === activeSession.settings.templateId);
      if (found) setSelectedTemplate(found);
    }
  }, [activeSession?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Auto-open chat and show preview on first generation ────────────────
  useEffect(() => {
    if (previewData && !prevPreviewRef.current) {
      setChatOpen(true);
      setShowSetup(false);
    }
    prevPreviewRef.current = previewData;
  }, [previewData]);

  // ── Load preview from session on switch ────────────────────────────────
  useEffect(() => {
    if (activeSession?.lastDownloadId) {
      setPreviewData({
        downloadId: activeSession.lastDownloadId,
        filename: activeSession.lastFilename || "Presentation.pptx",
        totalSlides: 0,
      });
      setShowSetup(false);
      fetch(`/api/preview/${activeSession.lastDownloadId}/info`)
        .then((r) => r.json())
        .then((d) => {
          if (d.total_slides > 0) {
            setPreviewData((prev) =>
              prev ? { ...prev, totalSlides: d.total_slides } : null,
            );
          }
        })
        .catch(() => {
          setPreviewData(null);
          setShowSetup(true);
        });
    } else {
      setPreviewData(null);
      setShowSetup(true);
    }
  }, [activeSession?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Auto-create first session ──────────────────────────────────────────
  useEffect(() => {
    if (sessions.sessions.length === 0) {
      createSession();
    } else if (!activeSessionId) {
      setActiveSessionId(sessions.sessions[0].id);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Handle template selection ──────────────────────────────────────────
  const handleSelectTemplate = useCallback(
    (t: Template) => {
      setSelectedTemplate(t);
      if (activeSessionId) {
        updateSettings(activeSessionId, {
          templateId: t.id,
          templateName: t.name,
        });
      }
    },
    [activeSessionId, updateSettings],
  );

  const handleUploadTemplate = useCallback(
    (f: File) => {
      setCustomTemplateFile(f);
      setSelectedTemplate(CUSTOM_UPLOAD_TEMPLATE);
      if (activeSessionId) {
        updateSettings(activeSessionId, {
          templateId: "custom-upload",
          templateName: f.name,
        });
      }
    },
    [activeSessionId, updateSettings],
  );

  // ── Handle settings changes ────────────────────────────────────────────
  const handleSettingsChange = useCallback(
    (changes: Partial<SessionSettings>) => {
      if (!activeSessionId) return;
      updateSettings(activeSessionId, changes);
    },
    [activeSessionId, updateSettings],
  );

  // ── Handle generate from workspace ─────────────────────────────────────
  const handleGenerate = useCallback(
    async (promptText: string) => {
      if (!activeSessionId || !activeSession || !selectedTemplate) return;

      const attachedPdf = pdfFile;

      // Add user message
      addMessage(
        activeSessionId,
        makeMessage({
          role: "user",
          content: promptText,
          attachments: attachedPdf
            ? [{ name: attachedPdf.name, type: attachedPdf.name.endsWith(".pdf") ? "pdf" : "md" }]
            : undefined,
        }),
      );

      // If in clarification mode
      if (pendingClarify) {
        setPendingClarify(false);
        const answers = { ...clarifyParams, answer: promptText };
        await generate({
          templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
          templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
          pdfFile: attachedPdf ?? undefined,
          purpose: activeSession.settings.purpose,
          language: activeSession.settings.language,
          userPrompt: promptText,
          clarifications: answers,
        });
        return;
      }

      // Try clarify first
      const questions = await clarify({
        templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
        templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
        pdfFile: attachedPdf ?? undefined,
        purpose: activeSession.settings.purpose,
        language: activeSession.settings.language,
        userPrompt: promptText,
      });

      if (questions && questions.length > 0) {
        setPendingClarify(true);
        setClarifyParams({ original_prompt: promptText });
        setChatOpen(true);
        return;
      }

      // Generate directly
      await generate({
        templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
        templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
        pdfFile: attachedPdf ?? undefined,
        purpose: activeSession.settings.purpose,
        language: activeSession.settings.language,
        userPrompt: promptText,
      });
    },
    [
      activeSessionId,
      activeSession,
      selectedTemplate,
      customTemplateFile,
      pdfFile,
      pendingClarify,
      clarifyParams,
      addMessage,
      generate,
      clarify,
    ],
  );

  // ── Handle chat send (for iteration / clarification) ───────────────────
  const handleChatSend = useCallback(
    async (text: string) => {
      if (!activeSessionId || !activeSession || !selectedTemplate) return;

      // Add user message
      addMessage(
        activeSessionId,
        makeMessage({ role: "user", content: text }),
      );

      // If clarifying
      if (pendingClarify) {
        setPendingClarify(false);
        const answers = { ...clarifyParams, answer: text };
        await generate({
          templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
          templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
          pdfFile: pdfFile ?? undefined,
          purpose: activeSession.settings.purpose,
          language: activeSession.settings.language,
          userPrompt: text,
          clarifications: answers,
        });
        return;
      }

      // Iterate on existing presentation
      if (previewData) {
        await iterate({
          downloadId: previewData.downloadId,
          feedback: text,
          templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
          templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
          purpose: activeSession.settings.purpose,
          language: activeSession.settings.language,
        });
        return;
      }

      // Fallback: generate
      await generate({
        templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
        templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
        pdfFile: pdfFile ?? undefined,
        purpose: activeSession.settings.purpose,
        language: activeSession.settings.language,
        userPrompt: text,
      });
    },
    [
      activeSessionId,
      activeSession,
      selectedTemplate,
      customTemplateFile,
      pdfFile,
      previewData,
      pendingClarify,
      clarifyParams,
      addMessage,
      generate,
      iterate,
    ],
  );

  // ── Handle new session ─────────────────────────────────────────────────
  const handleNewSession = useCallback(() => {
    createSession();
    setPreviewData(null);
    setPendingClarify(false);
    setPdfFile(null);
    setShowSetup(true);
    setChatOpen(false);
  }, [createSession, setPreviewData]);

  // ── Handle back to setup ───────────────────────────────────────────────
  const handleBackToSetup = useCallback(() => {
    setShowSetup(true);
  }, []);

  // ── View preview from chat ─────────────────────────────────────────────
  const handleViewPreview = useCallback(
    (downloadId: string) => {
      const msg = activeSession?.messages.find(
        (m) => m.previewData?.downloadId === downloadId,
      );
      if (msg?.previewData) {
        setPreviewData(msg.previewData);
        setShowSetup(false);
      }
    },
    [activeSession, setPreviewData],
  );

  // ── Session switch ─────────────────────────────────────────────────────
  const handleSelectSession = useCallback(
    (id: string) => {
      setActiveSessionId(id);
      setPendingClarify(false);
    },
    [setActiveSessionId],
  );

  const messages = activeSession?.messages ?? [];
  const workspacePreview = showSetup ? null : previewData;

  return (
    <div className="flex h-full bg-[#060609]">
      {/* ── History sidebar toggle (when closed) ───────────────────── */}
      {!historyOpen && (
        <button
          onClick={() => setHistoryOpen(true)}
          className="absolute top-3 left-3 z-20 p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-white/30 hover:text-white/60 transition-colors"
        >
          <PanelLeft className="w-4 h-4" />
        </button>
      )}

      {/* ── History sidebar ────────────────────────────────────────── */}
      <AnimatePresence>
        {historyOpen && (
          <HistorySidebar
            sessions={sessions.sessions}
            activeSessionId={activeSessionId}
            onSelect={handleSelectSession}
            onCreate={handleNewSession}
            onDelete={deleteSession}
            onClose={() => setHistoryOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* ── Workspace (center) ─────────────────────────────────────── */}
      <div className="flex-1 min-w-0">
        <WorkspacePanel
          preview={workspacePreview}
          settings={activeSession?.settings ?? { templateId: null, templateName: null, purpose: "business", language: "de" }}
          selectedTemplate={selectedTemplate}
          customFile={customTemplateFile}
          pdfFile={pdfFile}
          phase={phase}
          onSelectTemplate={handleSelectTemplate}
          onUploadTemplate={handleUploadTemplate}
          onUploadPdf={setPdfFile}
          onSettingsChange={handleSettingsChange}
          onGenerate={handleGenerate}
          onCancel={cancel}
          onBackToSetup={handleBackToSetup}
        />
      </div>

      {/* ── Chat toggle button (when closed) ───────────────────────── */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="absolute top-3 right-3 z-20 flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-white/30 hover:text-indigo-400 transition-colors"
          title="Open chat"
        >
          <MessageSquare className="w-4 h-4" />
          <span className="text-xs">Chat</span>
          {messages.length > 0 && (
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
          )}
        </button>
      )}

      {/* ── Chat sidebar (right, collapsible) ──────────────────────── */}
      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 380, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
            className="flex-shrink-0 overflow-hidden border-l border-white/[0.06]"
          >
            <div className="w-[380px] h-full flex flex-col bg-[#07070d]">
              {/* Chat header */}
              <div className="flex items-center justify-between px-3 py-2.5 border-b border-white/[0.06]">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-white/30" />
                  <span className="text-xs font-medium text-white/50">
                    {previewData ? "Feedback & Iteration" : "Chat"}
                  </span>
                </div>
                <button
                  onClick={() => setChatOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Chat panel */}
              <ChatPanel
                messages={messages}
                phase={phase}
                hasPreview={!!previewData}
                onSend={handleChatSend}
                onCancel={cancel}
                onViewPreview={handleViewPreview}
                onUploadPdf={setPdfFile}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Settings overlay ───────────────────────────────────────── */}
      <AnimatePresence>
        {settingsOpen && (
          <>
            <div
              className="fixed inset-0 bg-black/40 z-40"
              onClick={() => setSettingsOpen(false)}
            />
            <SettingsPanel
              settings={activeSession?.settings ?? { templateId: null, templateName: null, purpose: "business", language: "de" }}
              selectedTemplate={selectedTemplate}
              customFile={customTemplateFile}
              pdfFile={pdfFile}
              onSelectTemplate={handleSelectTemplate}
              onUploadTemplate={handleUploadTemplate}
              onUploadPdf={setPdfFile}
              onSettingsChange={handleSettingsChange}
              onClose={() => setSettingsOpen(false)}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
