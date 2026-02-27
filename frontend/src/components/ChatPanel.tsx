// ============================================================================
// SECTION: Imports
// ============================================================================

import { useRef, useEffect } from "react";
import { MessageSquare } from "lucide-react";
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
  onUploadPdf?: (file: File) => void;
}

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
  onUploadPdf: _onUploadPdf,
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
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3">
        {isEmpty ? (
          // ── Empty state for chat sidebar ──────────────────────────
          <div className="h-full flex flex-col items-center justify-center">
            <MessageSquare className="w-8 h-8 text-white/10 mb-3" />
            <p className="text-xs text-white/25 text-center max-w-[200px]">
              {hasPreview
                ? "Give feedback to refine your presentation."
                : "Generate a presentation first, then use chat for fine-tuning."}
            </p>
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
