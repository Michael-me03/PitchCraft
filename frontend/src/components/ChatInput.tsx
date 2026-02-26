// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useRef, useCallback } from "react";
import { Send, Paperclip, X, Loader2 } from "lucide-react";
import type { GenerationPhase } from "../types/chat";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  onSend: (text: string, file?: File) => void;
  onCancel: () => void;
  phase: GenerationPhase;
  hasPreview: boolean;
  disabled?: boolean;
}

// ============================================================================
// SECTION: Component
// ============================================================================

export default function ChatInput({ onSend, onCancel, phase, hasPreview, disabled }: Props) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isGenerating =
    phase === "generating" || phase === "converting" || phase === "clarifying" || phase === "rendering";

  const placeholder = hasPreview
    ? "Give feedback on your presentation..."
    : "Describe the presentation you want to create...";

  // ── Auto-resize textarea ───────────────────────────────────────────────
  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const val = e.target.value;
      if (val.length <= 2000) setText(val);
      // Auto-resize
      const ta = textareaRef.current;
      if (ta) {
        ta.style.height = "auto";
        ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
      }
    },
    [],
  );

  // ── Send handler ───────────────────────────────────────────────────────
  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed && !file) return;
    onSend(trimmed, file ?? undefined);
    setText("");
    setFile(null);
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [text, file, onSend]);

  // ── Keyboard ───────────────────────────────────────────────────────────
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  // ── File handler ───────────────────────────────────────────────────────
  const handleFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      const ext = f.name.toLowerCase().split(".").pop();
      if (ext === "pdf" || ext === "md") {
        setFile(f);
      }
    }
    e.target.value = "";
  }, []);

  return (
    <div className="border-t border-white/[0.06] bg-[#0a0a12]/80 backdrop-blur-xl p-3">
      {/* File chip */}
      {file && (
        <div className="mb-2 flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/15 border border-indigo-500/20 text-xs text-indigo-300">
            {file.name}
            <button
              onClick={() => setFile(null)}
              className="hover:text-white transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        </div>
      )}

      <div className="flex items-end gap-2">
        {/* Attach button */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={isGenerating || disabled}
          className={`p-2 rounded-lg transition-all disabled:opacity-30 ${!file && !hasPreview
              ? "bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 hover:text-indigo-300 ring-1 ring-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.1)]"
              : "hover:bg-white/[0.06] text-white/30 hover:text-white/60"
            }`}
          title="Attach PDF or Markdown (Recommended)"
        >
          <Paperclip className="w-4.5 h-4.5" />
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.md"
          onChange={handleFile}
          className="hidden"
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={isGenerating ? "Generating..." : placeholder}
          disabled={isGenerating || disabled}
          rows={1}
          className="flex-1 resize-none bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white/90 placeholder-white/25 focus:outline-none focus:border-indigo-500/40 transition-colors disabled:opacity-40"
          style={{ minHeight: "42px", maxHeight: "160px" }}
        />

        {/* Send / Cancel button */}
        {isGenerating ? (
          <button
            onClick={onCancel}
            className="p-2.5 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors"
            title="Cancel generation"
          >
            <X className="w-4.5 h-4.5" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={(!text.trim() && !file) || disabled}
            className="p-2.5 rounded-xl bg-indigo-600/80 hover:bg-indigo-600 text-white transition-colors disabled:opacity-30 disabled:hover:bg-indigo-600/80"
            title="Send message"
          >
            {phase === "done" || phase === "error" || phase === "idle" ? (
              <Send className="w-4.5 h-4.5" />
            ) : (
              <Loader2 className="w-4.5 h-4.5 animate-spin" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}
