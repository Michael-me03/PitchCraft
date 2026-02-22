import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FileSearch,
  BrainCircuit,
  LayoutPanelTop,
  Download,
  Check,
} from "lucide-react";

const STEPS = [
  {
    label: "Reading PDF",
    description: "Extracting text and structure",
    icon: FileSearch,
    duration: 3000,
  },
  {
    label: "AI Analysis",
    description: "Generating slide structure & charts",
    icon: BrainCircuit,
    duration: 15000,
  },
  {
    label: "Building Slides",
    description: "Applying template & formatting",
    icon: LayoutPanelTop,
    duration: 5000,
  },
  {
    label: "Finalizing",
    description: "Preparing download",
    icon: Download,
    duration: 2000,
  },
];

export default function ProgressIndicator() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    let elapsed = 0;
    STEPS.forEach((_step, i) => {
      if (i > 0) {
        elapsed += STEPS[i - 1].duration;
        timers.push(setTimeout(() => setActiveStep(i), elapsed));
      }
    });
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.4 }}
      className="rounded-2xl p-6 bg-white/[0.02] border border-white/[0.04]"
    >
      {/* Animated orb */}
      <div className="flex justify-center mb-6">
        <div className="relative">
          <motion.div
            animate={{
              boxShadow: [
                "0 0 20px 4px rgba(99,102,241,0.2)",
                "0 0 40px 8px rgba(139,92,246,0.3)",
                "0 0 20px 4px rgba(99,102,241,0.2)",
              ],
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/20 flex items-center justify-center"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
              className="w-10 h-10 rounded-full border-2 border-transparent border-t-indigo-400/60 border-r-violet-400/30"
            />
          </motion.div>
          <motion.div
            animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute inset-0 rounded-full bg-indigo-500/10"
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-1">
        {STEPS.map((step, i) => {
          const isActive = i === activeStep;
          const isDone = i < activeStep;
          const StepIcon = isDone ? Check : step.icon;

          return (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-500 ${
                isActive
                  ? "bg-indigo-500/[0.06]"
                  : ""
              }`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-500 ${
                  isDone
                    ? "bg-emerald-500/10 border border-emerald-500/20"
                    : isActive
                    ? "bg-indigo-500/10 border border-indigo-500/20"
                    : "bg-white/[0.02] border border-white/[0.04]"
                }`}
              >
                <StepIcon
                  className={`w-3.5 h-3.5 transition-colors duration-500 ${
                    isDone
                      ? "text-emerald-400"
                      : isActive
                      ? "text-indigo-400"
                      : "text-gray-700"
                  }`}
                />
              </div>

              <div className="flex-1 min-w-0">
                <p
                  className={`text-[13px] font-medium transition-colors duration-500 ${
                    isDone
                      ? "text-emerald-400/80"
                      : isActive
                      ? "text-gray-200"
                      : "text-gray-600"
                  }`}
                >
                  {step.label}
                </p>
                {isActive && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="text-[11px] text-gray-500 mt-0.5"
                  >
                    {step.description}
                  </motion.p>
                )}
              </div>

              {isActive && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0"
                />
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="mt-5 h-[2px] bg-white/[0.04] rounded-full overflow-hidden">
        <motion.div
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration: 25, ease: "linear" }}
          className="h-full bg-gradient-to-r from-indigo-500/50 via-violet-500/50 to-indigo-500/50 rounded-full"
        />
      </div>
    </motion.div>
  );
}
