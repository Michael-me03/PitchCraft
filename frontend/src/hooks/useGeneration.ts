// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useRef, useCallback } from "react";
import axios from "axios";
import type {
  ChatMessage,
  GenerationPhase,
  PreviewData,
  ClarifyQuestion,
} from "../types/chat";

// ============================================================================
// SECTION: Constants
// ============================================================================

const API_URL = "";
const GENERATE_TIMEOUT = 600_000; // 10 minutes
const CLARIFY_TIMEOUT = 30_000;   // 30 seconds

// ============================================================================
// SECTION: Types
// ============================================================================

interface GenerateParams {
  templateId?: string;
  templateFile?: File;
  pdfFile?: File;
  purpose: string;
  language: string;
  userPrompt: string;
  clarifications?: Record<string, string>;
}

interface IterateParams {
  downloadId: string;
  feedback: string;
  templateId?: string;
  templateFile?: File;
  purpose: string;
  language: string;
}

// ============================================================================
// SECTION: Helper — Build message
// ============================================================================

function makeMessage(partial: Omit<ChatMessage, "id" | "timestamp">): ChatMessage {
  const id =
    crypto.randomUUID?.() ??
    `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  return { ...partial, id, timestamp: Date.now() };
}

// ============================================================================
// SECTION: Hook
// ============================================================================

export function useGeneration(
  addMessage: (sessionId: string, msg: ChatMessage) => void,
  activeSessionId: string | null,
  updateSession?: (sessionId: string, updates: Record<string, unknown>) => void,
) {
  const [phase, setPhase] = useState<GenerationPhase>("idle");
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // ── Cancel ───────────────────────────────────────────────────────────────
  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setPhase("idle");
    if (activeSessionId) {
      addMessage(
        activeSessionId,
        makeMessage({ role: "system", content: "Generation cancelled." }),
      );
    }
  }, [activeSessionId, addMessage]);

  // ── Clarify ──────────────────────────────────────────────────────────────
  const clarify = useCallback(
    async (params: GenerateParams): Promise<ClarifyQuestion[] | null> => {
      if (!activeSessionId) return null;

      setPhase("clarifying");
      try {
        const fd = new FormData();
        fd.append("user_prompt", params.userPrompt);
        fd.append("purpose", params.purpose);
        fd.append("language", params.language);
        if (params.pdfFile) fd.append("pdf_file", params.pdfFile);

        const res = await axios.post(`${API_URL}/api/clarify`, fd, {
          timeout: CLARIFY_TIMEOUT,
        });

        const { needs_clarification, questions } = res.data;
        if (needs_clarification && questions?.length > 0) {
          addMessage(
            activeSessionId,
            makeMessage({
              role: "assistant",
              content: "I have a few questions to make your presentation better:",
              clarifyQuestions: questions,
            }),
          );
          return questions;
        }
      } catch {
        // Clarify failure is non-fatal — skip and proceed
      }
      return null;
    },
    [activeSessionId, addMessage],
  );

  // ── Generate ─────────────────────────────────────────────────────────────
  const generate = useCallback(
    async (params: GenerateParams): Promise<void> => {
      if (!activeSessionId) return;

      const controller = new AbortController();
      abortRef.current = controller;

      setPhase("generating");
      addMessage(
        activeSessionId,
        makeMessage({
          role: "assistant",
          content: "Generating your presentation...",
        }),
      );

      try {
        const fd = new FormData();
        if (params.templateFile) {
          fd.append("template_file", params.templateFile);
        } else if (params.templateId) {
          fd.append("template_id", params.templateId);
        }
        fd.append("user_prompt", params.userPrompt);
        fd.append("purpose", params.purpose);
        fd.append("language", params.language);
        if (params.pdfFile) fd.append("pdf_file", params.pdfFile);
        if (params.clarifications) {
          fd.append("clarifications", JSON.stringify(params.clarifications));
        }

        const res = await axios.post(`${API_URL}/api/generate`, fd, {
          timeout: GENERATE_TIMEOUT,
          signal: controller.signal,
        });

        const { download_id, filename, quality_report } = res.data;

        // Add thinking blocks
        if (quality_report?.history) {
          for (const entry of quality_report.history) {
            addMessage(
              activeSessionId,
              makeMessage({
                role: "thinking",
                content: entry.reasoning || "",
                thinkingData: entry,
              }),
            );
          }
        }

        // Fetch preview info
        setPhase("converting");
        let totalSlides = 0;
        try {
          const previewRes = await axios.get(
            `${API_URL}/api/preview/${download_id}/info`,
            { signal: controller.signal },
          );
          totalSlides = previewRes.data.total_slides || 0;
        } catch {
          // Preview may fail if LibreOffice is not installed
        }

        const preview: PreviewData = {
          downloadId: download_id,
          filename,
          totalSlides,
        };
        setPreviewData(preview);

        // Add preview message
        addMessage(
          activeSessionId,
          makeMessage({
            role: "preview",
            content: `Your presentation "${filename}" is ready!`,
            previewData: preview,
          }),
        );

        // Store download info on session
        if (updateSession) {
          updateSession(activeSessionId, {
            lastDownloadId: download_id,
            lastFilename: filename,
          });
        }

        setPhase("done");
      } catch (err) {
        if (axios.isCancel(err)) return;

        const detail =
          axios.isAxiosError(err) && err.response?.data?.detail
            ? err.response.data.detail
            : axios.isAxiosError(err) && err.code === "ECONNABORTED"
              ? "Generation timed out. Please try a shorter prompt."
              : "Generation failed. Please try again.";

        addMessage(
          activeSessionId,
          makeMessage({ role: "assistant", content: `Error: ${detail}` }),
        );
        setPhase("error");
      } finally {
        abortRef.current = null;
      }
    },
    [activeSessionId, addMessage, updateSession],
  );

  // ── Iterate ──────────────────────────────────────────────────────────────
  const iterate = useCallback(
    async (params: IterateParams): Promise<void> => {
      if (!activeSessionId) return;

      const controller = new AbortController();
      abortRef.current = controller;

      setPhase("generating");
      addMessage(
        activeSessionId,
        makeMessage({
          role: "assistant",
          content: "Updating your presentation based on feedback...",
        }),
      );

      try {
        const fd = new FormData();
        fd.append("download_id", params.downloadId);
        fd.append("feedback", params.feedback);
        if (params.templateFile) {
          fd.append("template_file", params.templateFile);
        } else if (params.templateId) {
          fd.append("template_id", params.templateId);
        }
        fd.append("purpose", params.purpose);
        fd.append("language", params.language);

        const res = await axios.post(`${API_URL}/api/generate-iterate`, fd, {
          timeout: GENERATE_TIMEOUT,
          signal: controller.signal,
        });

        const { download_id, filename, quality_report } = res.data;

        // Add thinking blocks
        if (quality_report?.history) {
          for (const entry of quality_report.history) {
            addMessage(
              activeSessionId,
              makeMessage({
                role: "thinking",
                content: entry.reasoning || "",
                thinkingData: entry,
              }),
            );
          }
        }

        // Fetch preview info
        setPhase("converting");
        let totalSlides = 0;
        try {
          const previewRes = await axios.get(
            `${API_URL}/api/preview/${download_id}/info`,
            { signal: controller.signal },
          );
          totalSlides = previewRes.data.total_slides || 0;
        } catch {
          // Preview may fail
        }

        const preview: PreviewData = {
          downloadId: download_id,
          filename,
          totalSlides,
        };
        setPreviewData(preview);

        addMessage(
          activeSessionId,
          makeMessage({
            role: "preview",
            content: `Updated presentation "${filename}" is ready!`,
            previewData: preview,
          }),
        );

        if (updateSession) {
          updateSession(activeSessionId, {
            lastDownloadId: download_id,
            lastFilename: filename,
          });
        }

        setPhase("done");
      } catch (err) {
        if (axios.isCancel(err)) return;

        const detail =
          axios.isAxiosError(err) && err.response?.data?.detail
            ? err.response.data.detail
            : "Iteration failed. Please try again.";

        addMessage(
          activeSessionId,
          makeMessage({ role: "assistant", content: `Error: ${detail}` }),
        );
        setPhase("error");
      } finally {
        abortRef.current = null;
      }
    },
    [activeSessionId, addMessage, updateSession],
  );

  return { phase, previewData, setPreviewData, generate, iterate, clarify, cancel };
}
