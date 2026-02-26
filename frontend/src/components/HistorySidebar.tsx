// ============================================================================
// SECTION: Imports
// ============================================================================

import { motion } from "framer-motion";
import { Plus, MessageSquare, Trash2, PanelLeftClose } from "lucide-react";
import type { ChatSession } from "../types/chat";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}

// ============================================================================
// SECTION: Helpers
// ============================================================================

function timeAgo(ts: number): string {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ============================================================================
// SECTION: Component
// ============================================================================

export default function HistorySidebar({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
  onDelete,
  onClose,
}: Props) {
  const sorted = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <motion.div
      initial={{ x: -260, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -260, opacity: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 300 }}
      className="w-[260px] h-full flex flex-col bg-[#08080f] border-r border-white/[0.06]"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-white/[0.06]">
        <button
          onClick={onCreate}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-medium transition-colors flex-1"
        >
          <Plus className="w-3.5 h-3.5" />
          New Chat
        </button>
        <button
          onClick={onClose}
          className="ml-2 p-2 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-1">
        {sorted.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-xs text-white/20">No conversations yet</p>
          </div>
        ) : (
          sorted.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                onClick={() => onSelect(session.id)}
                className={`group flex items-center gap-2 mx-2 my-0.5 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                  isActive
                    ? "bg-white/[0.08] text-white/90"
                    : "text-white/50 hover:bg-white/[0.04] hover:text-white/70"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-40" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">{session.title}</p>
                  <p className="text-[10px] text-white/25 mt-0.5">
                    {timeAgo(session.updatedAt)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-white/[0.08] text-white/30 hover:text-red-400 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}
