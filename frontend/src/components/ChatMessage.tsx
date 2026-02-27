// ============================================================================
// SECTION: Imports
// ============================================================================

import { motion } from "framer-motion";
import { User, Bot, Info, Presentation } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "../types/chat";
import ThinkingBlock from "./ThinkingBlock";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  message: ChatMessageType;
  onViewPreview?: (downloadId: string) => void;
}

// ============================================================================
// SECTION: Component
// ============================================================================

export default function ChatMessage({ message, onViewPreview }: Props) {
  // ── System messages ────────────────────────────────────────────────────
  if (message.role === "system") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex justify-center my-2"
      >
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.04] text-white/40 text-xs">
          <Info className="w-3 h-3" />
          {message.content}
        </div>
      </motion.div>
    );
  }

  // ── Thinking blocks ────────────────────────────────────────────────────
  if (message.role === "thinking" && message.thinkingData) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-start"
      >
        <ThinkingBlock data={message.thinkingData} />
      </motion.div>
    );
  }

  // ── Preview card ───────────────────────────────────────────────────────
  if (message.role === "preview" && message.previewData) {
    const { downloadId, filename, totalSlides } = message.previewData;
    // Extract summary lines from content (after the "is ready!" prefix)
    const summaryPart = message.content.split(" — ").slice(1).join(" — ");
    const summaryLines = summaryPart ? summaryPart.split("\n").filter(Boolean) : [];
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-start my-2"
      >
        <div className="max-w-[480px] rounded-xl bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/20 p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
              <Presentation className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white/90">{filename}</p>
              <p className="text-xs text-white/40">
                {totalSlides > 0 ? `${totalSlides} slides` : "Ready to download"}
              </p>
            </div>
          </div>
          {summaryLines.length > 0 && (
            <div className="mb-3 pl-1 space-y-1">
              {summaryLines.map((line, idx) => (
                <p
                  key={idx}
                  className="text-xs text-white/50 leading-relaxed"
                  dangerouslySetInnerHTML={{
                    __html: line
                      .replace(/\*\*(.*?)\*\*/g, '<span class="text-white/80 font-medium">$1</span>')
                  }}
                />
              ))}
            </div>
          )}
          <div className="flex gap-2">
            {totalSlides > 0 && onViewPreview && (
              <button
                onClick={() => onViewPreview(downloadId)}
                className="flex-1 py-2 px-3 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 text-xs font-medium transition-colors"
              >
                View Slides
              </button>
            )}
            <a
              href={`/api/download/${downloadId}`}
              download={filename}
              className="flex-1 py-2 px-3 rounded-lg bg-white/[0.08] hover:bg-white/[0.12] text-white/80 text-xs font-medium text-center transition-colors"
            >
              Download
            </a>
          </div>
        </div>
      </motion.div>
    );
  }

  // ── User message ───────────────────────────────────────────────────────
  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end my-2"
      >
        <div className="max-w-[480px] flex items-start gap-2">
          <div className="rounded-2xl rounded-tr-md px-4 py-2.5 bg-indigo-600/30 border border-indigo-500/20 text-sm text-white/90 leading-relaxed">
            {message.content}
            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {message.attachments.map((att, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/[0.08] text-xs text-white/50"
                  >
                    {att.name}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="w-7 h-7 rounded-full bg-indigo-600/30 flex items-center justify-center flex-shrink-0 mt-0.5">
            <User className="w-3.5 h-3.5 text-indigo-300" />
          </div>
        </div>
      </motion.div>
    );
  }

  // ── Assistant message ──────────────────────────────────────────────────
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start my-2"
    >
      <div className="max-w-[480px] flex items-start gap-2">
        <div className="w-7 h-7 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot className="w-3.5 h-3.5 text-white/50" />
        </div>
        <div className="rounded-2xl rounded-tl-md px-4 py-2.5 bg-white/[0.04] border border-white/[0.06] text-sm text-white/80 leading-relaxed">
          {message.content}
          {/* Clarify questions inline */}
          {message.clarifyQuestions && message.clarifyQuestions.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.clarifyQuestions.map((q) => (
                <div
                  key={q.id}
                  className="p-2 rounded-lg bg-white/[0.04] border border-white/[0.06]"
                >
                  <p className="text-xs text-white/70 font-medium">{q.question}</p>
                  {q.hint && (
                    <p className="text-xs text-white/30 mt-0.5">{q.hint}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
