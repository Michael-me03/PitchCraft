// ============================================================================
// SECTION: Imports
// ============================================================================

import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  onDismiss: () => void;
}

// ============================================================================
// SECTION: Component
// ============================================================================

export default function WelcomeOverlay({ onDismiss }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.05, filter: "blur(8px)" }}
      transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      className="fixed inset-0 z-[100] flex items-center justify-center"
      style={{ background: "rgba(6, 6, 9, 0.92)", backdropFilter: "blur(20px)" }}
    >
      {/* ── Ambient glow ─────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, delay: 0.2 }}
        className="absolute pointer-events-none"
        style={{
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%)",
          filter: "blur(60px)",
        }}
      />

      {/* ── Content ──────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15, ease: [0.4, 0, 0.2, 1] }}
        className="relative flex flex-col items-center text-center max-w-md mx-4"
      >
        {/* Icon with pulse ring */}
        <div className="relative mb-8">
          <motion.div
            animate={{ scale: [1, 1.15, 1] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            className="absolute inset-0 rounded-2xl"
            style={{
              background: "rgba(99, 102, 241, 0.15)",
              border: "1px solid rgba(99, 102, 241, 0.4)",
              boxShadow: "0 0 40px rgba(99, 102, 241, 0.25)",
            }}
          />
          <div className="relative w-16 h-16 rounded-2xl flex items-center justify-center text-indigo-300">
            <Sparkles className="w-7 h-7" />
          </div>
        </div>

        {/* Text */}
        <h2 className="text-2xl font-bold text-white/95 mb-3">
          Welcome to PitchCraft
        </h2>
        <p className="text-sm text-white/50 leading-relaxed max-w-sm mb-10">
          Transform your ideas into stunning presentations with AI.
          Describe what you need, upload a source document, and iterate
          until it's perfect.
        </p>

        {/* Button */}
        <motion.button
          onClick={onDismiss}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-medium transition-colors"
          style={{
            background: "linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(99, 102, 241, 0.25))",
            border: "1px solid rgba(99, 102, 241, 0.4)",
            color: "#a5b4fc",
          }}
        >
          Get Started
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
