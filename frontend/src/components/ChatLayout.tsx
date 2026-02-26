// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useCallback, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { PanelLeft } from "lucide-react";
import { TEMPLATES } from "../data/templates";
import type { Template } from "../types/template";
import type { ChatMessage, SessionSettings } from "../types/chat";
import { useChatSessions } from "../hooks/useChatSessions";
import { useGeneration } from "../hooks/useGeneration";
import HistorySidebar from "./HistorySidebar";
import ChatPanel from "./ChatPanel";
import PreviewPanel from "./PreviewPanel";
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
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    TEMPLATES[0] ?? null,
  );
  const [customTemplateFile, setCustomTemplateFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pendingClarify, setPendingClarify] = useState(false);
  const [clarifyParams, setClarifyParams] = useState<Record<string, string>>({});

  // ── Sync template from session settings ────────────────────────────────
  useEffect(() => {
    if (activeSession?.settings.templateId) {
      const found = TEMPLATES.find((t) => t.id === activeSession.settings.templateId);
      if (found) setSelectedTemplate(found);
    }
  }, [activeSession?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Load preview from session on switch ────────────────────────────────
  useEffect(() => {
    if (activeSession?.lastDownloadId) {
      // Try to load preview for the last download
      setPreviewData({
        downloadId: activeSession.lastDownloadId,
        filename: activeSession.lastFilename || "Presentation.pptx",
        totalSlides: 0, // Will be fetched lazily
      });
      // Fetch actual slide count
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
          // Preview may have expired
          setPreviewData(null);
        });
    } else {
      setPreviewData(null);
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
        addMessage(
          activeSessionId,
          makeMessage({
            role: "system",
            content: `Template changed to "${t.name}"`,
          }),
        );
      }
    },
    [activeSessionId, updateSettings, addMessage],
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
        addMessage(
          activeSessionId,
          makeMessage({
            role: "system",
            content: `Custom template uploaded: ${f.name}`,
          }),
        );
      }
    },
    [activeSessionId, updateSettings, addMessage],
  );

  // ── Handle settings changes ────────────────────────────────────────────
  const handleSettingsChange = useCallback(
    (changes: Partial<SessionSettings>) => {
      if (!activeSessionId) return;
      updateSettings(activeSessionId, changes);

      if (changes.language) {
        const langNames: Record<string, string> = {
          de: "Deutsch",
          en: "English",
          fr: "Français",
          es: "Español",
        };
        addMessage(
          activeSessionId,
          makeMessage({
            role: "system",
            content: `Language changed to ${langNames[changes.language] || changes.language}`,
          }),
        );
      }
      if (changes.purpose) {
        addMessage(
          activeSessionId,
          makeMessage({
            role: "system",
            content: `Style changed to ${changes.purpose}`,
          }),
        );
      }
    },
    [activeSessionId, updateSettings, addMessage],
  );

  // ── Handle send ────────────────────────────────────────────────────────
  const handleSend = useCallback(
    async (text: string, file?: File) => {
      if (!activeSessionId || !activeSession) return;

      const attachedPdf = file || pdfFile;

      // Ensure template is selected
      if (!selectedTemplate) {
        addMessage(
          activeSessionId,
          makeMessage({
            role: "assistant",
            content: "Please select a template first. Open Settings (gear icon) to choose one.",
          }),
        );
        return;
      }

      // Add user message
      addMessage(
        activeSessionId,
        makeMessage({
          role: "user",
          content: text,
          attachments: attachedPdf
            ? [{ name: attachedPdf.name, type: attachedPdf.name.endsWith(".pdf") ? "pdf" : "md" }]
            : undefined,
        }),
      );

      // If we're in clarification mode (answering questions)
      if (pendingClarify) {
        setPendingClarify(false);
        const answers = { ...clarifyParams, answer: text };

        await generate({
          templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
          templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
          pdfFile: attachedPdf ?? undefined,
          purpose: activeSession.settings.purpose,
          language: activeSession.settings.language,
          userPrompt: text,
          clarifications: answers,
        });
        return;
      }

      // If we already have a preview → iterate
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

      // First generation — try clarify first
      const questions = await clarify({
        templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
        templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
        pdfFile: attachedPdf ?? undefined,
        purpose: activeSession.settings.purpose,
        language: activeSession.settings.language,
        userPrompt: text,
      });

      if (questions && questions.length > 0) {
        setPendingClarify(true);
        setClarifyParams({ original_prompt: text });
        return;
      }

      // No clarification needed → generate directly
      await generate({
        templateId: selectedTemplate.id === "custom-upload" ? undefined : selectedTemplate.id,
        templateFile: selectedTemplate.id === "custom-upload" ? customTemplateFile ?? undefined : undefined,
        pdfFile: attachedPdf ?? undefined,
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
      clarify,
    ],
  );

  // ── Handle new session ─────────────────────────────────────────────────
  const handleNewSession = useCallback(() => {
    createSession();
    setPreviewData(null);
    setPendingClarify(false);
    setPdfFile(null);
  }, [createSession, setPreviewData]);

  // ── View preview from chat ─────────────────────────────────────────────
  const handleViewPreview = useCallback(
    (downloadId: string) => {
      // Find the preview data in messages
      const msg = activeSession?.messages.find(
        (m) => m.previewData?.downloadId === downloadId,
      );
      if (msg?.previewData) {
        setPreviewData(msg.previewData);
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
  const hasPreview = previewData !== null;

  return (
    <div className="flex h-full bg-[#060609]">
      {/* History sidebar toggle (when closed) */}
      {!historyOpen && (
        <button
          onClick={() => setHistoryOpen(true)}
          className="absolute top-3 left-3 z-20 p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-white/30 hover:text-white/60 transition-colors"
        >
          <PanelLeft className="w-4 h-4" />
        </button>
      )}

      {/* History sidebar */}
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

      {/* Chat panel */}
      <div className={`flex-1 min-w-0 ${hasPreview ? "" : ""}`}>
        <ChatPanel
          messages={messages}
          phase={phase}
          hasPreview={hasPreview}
          onSend={handleSend}
          onCancel={cancel}
          onViewPreview={handleViewPreview}
        />
      </div>

      {/* Preview panel */}
      {hasPreview && (
        <div className="w-[50%] min-w-[400px] max-w-[700px]">
          <PreviewPanel
            preview={previewData}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        </div>
      )}

      {/* Preview placeholder (when no preview but needs settings access) */}
      {!hasPreview && (
        <div className="w-[50%] min-w-[400px] max-w-[700px]">
          <PreviewPanel
            preview={null}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        </div>
      )}

      {/* Settings overlay */}
      <AnimatePresence>
        {settingsOpen && (
          <>
            {/* Backdrop */}
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
