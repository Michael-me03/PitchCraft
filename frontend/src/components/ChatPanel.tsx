// ============================================================================
// SECTION: Imports
// ============================================================================

import { useRef, useEffect } from "react";
import { Sparkles, FileText, Upload } from "lucide-react";
import type { ChatMessage as ChatMessageType, GenerationPhase } from "../types/chat";
import ChatMessageComponent from "./ChatMessage";
import ChatInput from "./ChatInput";
import GenerationProgress from "./GenerationProgress";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  messages: ChatMessageType[];
  phase: GenerationPhase;
  hasPreview: boolean;
  onSend: (text: string, file?: File) => void;
  onCancel: () => void;
  onViewPreview: (downloadId: string) => void;
  onUploadPdf: (file: File) => void;
}

// ============================================================================
// SECTION: Starter Prompts
// ============================================================================

const STARTERS = [
  "Create a Q3 investor update with revenue charts and KPIs",
  "Build a pitch deck for an AI startup raising Series A",
  "Make a scientific presentation about climate change data",
  "Design a school presentation about the solar system",
];

// ============================================================================
// SECTION: Component
// ============================================================================

export default function ChatPanel({
  messages,
  phase,
  hasPreview,
  onSend,
  onCancel,
  onViewPreview,
  onUploadPdf,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadPdf(file);
    }
  };

  // ── Auto-scroll ────────────────────────────────────────────────────────
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, phase]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full">
      {/* Message area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        {isEmpty ? (
          // ── Empty state ────────────────────────────────────────────
          <div className="h-full flex flex-col items-center justify-center">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 flex items-center justify-center mb-4">
              <Sparkles className="w-7 h-7 text-indigo-400" />
            </div>
            <h2 className="text-xl font-semibold text-white/90 mb-1">
              PitchCraft
            </h2>
            <p className="text-sm text-white/40 mb-8 text-center max-w-xs">
              AI-powered presentation generator. Use a source file for best results,
              or describe what you need below.
            </p>

            {/* ── Main Context Upload Card ────────────────────────────────── */}
            <div className="w-full max-w-md mb-8 px-4">
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".pdf,.md"
                onChange={handleFileChange}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full relative group p-6 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 hover:bg-indigo-500/10 hover:border-indigo-500/40 transition-all text-left overflow-hidden"
              >
                {/* Visual pulse effect */}
                <div className="absolute inset-0 bg-indigo-500/5 group-hover:bg-indigo-500/10 transition-colors animate-pulse pointer-events-none" />

                <div className="flex items-start gap-4 relative z-10">
                  <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center shrink-0">
                    <FileText className="w-6 h-6 text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-white/90 font-medium mb-1 flex items-center gap-2">
                      Upload Source Document
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold uppercase tracking-wider">
                        Recommended
                      </span>
                    </h3>
                    <p className="text-xs text-white/40 leading-relaxed">
                      Upload a PDF or Markdown file. A source document provides the
                      essential context I need to build a high-quality presentation.
                    </p>
                  </div>
                  <div className="ml-auto self-center p-2 rounded-lg bg-white/5 text-white/40 group-hover:text-indigo-400 group-hover:bg-indigo-500/10 transition-all">
                    <Upload className="w-4 h-4" />
                  </div>
                </div>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
              {STARTERS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => onSend(prompt)}
                  className="text-left p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] hover:border-white/[0.1] text-xs text-white/50 hover:text-white/70 transition-all"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          // ── Message stream ─────────────────────────────────────────
          <div className="space-y-1">
            {messages.map((msg) => (
              <ChatMessageComponent
                key={msg.id}
                message={msg}
                onViewPreview={onViewPreview}
              />
            ))}
            <GenerationProgress phase={phase} />
          </div>
        )}
      </div>

      {/* Input bar */}
      <ChatInput
        onSend={onSend}
        onCancel={onCancel}
        phase={phase}
        hasPreview={hasPreview}
      />
    </div>
  );
}
