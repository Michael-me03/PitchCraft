// ============================================================================
// SECTION: Imports
// ============================================================================

import { useRef, useEffect } from "react";
import { Sparkles } from "lucide-react";
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
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

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
              AI-powered presentation generator. Describe what you need and
              I'll create it.
            </p>
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
