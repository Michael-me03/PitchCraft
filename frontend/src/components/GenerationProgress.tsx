// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FileSearch,
  BrainCircuit,
  LayoutPanelTop,
  Download,
  Check,
  Loader2,
} from "lucide-react";
import type { GenerationPhase } from "../types/chat";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  phase: GenerationPhase;
}

// ============================================================================
// SECTION: Step Configuration
// ============================================================================

const STEPS = [
  { label: "Reading content", icon: FileSearch, duration: 3000 },
  { label: "AI analysis", icon: BrainCircuit, duration: 18000 },
  { label: "Building slides", icon: LayoutPanelTop, duration: 6000 },
  { label: "Finalizing", icon: Download, duration: 3000 },
];

// ============================================================================
// SECTION: Component
// ============================================================================

export default function GenerationProgress({ phase }: Props) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (phase !== "generating" && phase !== "converting" && phase !== "rendering") {
      setActiveStep(0);
      return;
    }

    let elapsed = 0;
    const interval = setInterval(() => {
      elapsed += 500;
      let cumulative = 0;
      for (let i = 0; i < STEPS.length; i++) {
        cumulative += STEPS[i].duration;
        if (elapsed < cumulative) {
          setActiveStep(i);
          return;
        }
      }
      setActiveStep(STEPS.length - 1);
    }, 500);

    return () => clearInterval(interval);
  }, [phase]);

  if (phase !== "generating" && phase !== "converting" && phase !== "rendering") {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start my-2"
    >
      <div className="max-w-[360px] rounded-xl bg-white/[0.03] border border-white/[0.06] p-3">
        <div className="space-y-2">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            const isDone = i < activeStep;
            const isActive = i === activeStep;

            return (
              <div
                key={i}
                className={`flex items-center gap-2.5 text-xs transition-colors ${
                  isDone
                    ? "text-emerald-400/70"
                    : isActive
                      ? "text-white/80"
                      : "text-white/20"
                }`}
              >
                <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                  {isDone ? (
                    <Check className="w-3.5 h-3.5" />
                  ) : isActive ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Icon className="w-3.5 h-3.5" />
                  )}
                </div>
                <span className={isActive ? "font-medium" : ""}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
