// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight, CheckCircle2, AlertTriangle } from "lucide-react";
import type { QualityLoopEntry } from "../types/chat";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  data: QualityLoopEntry;
}

// ============================================================================
// SECTION: Component
// ============================================================================

export default function ThinkingBlock({ data }: Props) {
  const [expanded, setExpanded] = useState(false);
  const isGood = data.verdict === "good" || data.verdict === "skipped";

  return (
    <div className="my-2 max-w-[480px]">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-white/50 hover:text-white/80 transition-colors w-full text-left"
      >
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" />
        )}
        {isGood ? (
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
        ) : (
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
        )}
        <span>
          Thinking (Attempt {data.attempt}:{" "}
          <span className={isGood ? "text-emerald-400" : "text-amber-400"}>
            {data.verdict.toUpperCase()}
          </span>
          )
        </span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-2 ml-5 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs text-white/60 space-y-2">
              {data.reasoning && <p>{data.reasoning}</p>}
              {data.issues.length > 0 && (
                <div>
                  <p className="text-amber-400/80 font-medium mb-1">Issues:</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {data.issues.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
