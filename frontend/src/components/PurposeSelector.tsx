import { motion, AnimatePresence } from "framer-motion";
import {
  Briefcase,
  GraduationCap,
  FlaskConical,
  Pen,
  type LucideIcon,
} from "lucide-react";

interface Purpose {
  id: string;
  label: string;
  icon: LucideIcon;
  description: string;
  gradient: string;
  iconColor: string;
  activeGlow: string;
}

const PURPOSES: Purpose[] = [
  {
    id: "business",
    label: "Business",
    icon: Briefcase,
    description: "Corporate, KPI-driven, executive-ready",
    gradient: "from-blue-500/20 to-indigo-500/20",
    iconColor: "#60a5fa",
    activeGlow: "rgba(96, 165, 250, 0.15)",
  },
  {
    id: "school",
    label: "Education",
    icon: GraduationCap,
    description: "Clear, visual, student-friendly",
    gradient: "from-emerald-500/20 to-teal-500/20",
    iconColor: "#34d399",
    activeGlow: "rgba(52, 211, 153, 0.15)",
  },
  {
    id: "scientific",
    label: "Scientific",
    icon: FlaskConical,
    description: "Data-focused, academic, precise",
    gradient: "from-violet-500/20 to-purple-500/20",
    iconColor: "#a78bfa",
    activeGlow: "rgba(167, 139, 250, 0.15)",
  },
  {
    id: "custom",
    label: "Custom",
    icon: Pen,
    description: "Your own style & instructions",
    gradient: "from-orange-500/20 to-amber-500/20",
    iconColor: "#fb923c",
    activeGlow: "rgba(251, 146, 60, 0.15)",
  },
];

interface PurposeSelectorProps {
  purpose: string;
  customPrompt: string;
  onPurposeChange: (purpose: string) => void;
  onCustomPromptChange: (prompt: string) => void;
}

export default function PurposeSelector({
  purpose,
  customPrompt,
  onPurposeChange,
  onCustomPromptChange,
}: PurposeSelectorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="flex items-center gap-2 mb-5">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
        <span className="text-[11px] font-medium tracking-[0.15em] uppercase text-gray-500">
          Presentation Style
        </span>
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {PURPOSES.map((p, i) => {
          const isActive = purpose === p.id;
          return (
            <motion.button
              key={p.id}
              onClick={() => onPurposeChange(p.id)}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.5,
                delay: 0.25 + i * 0.06,
                ease: [0.22, 1, 0.36, 1],
              }}
              whileTap={{ scale: 0.97 }}
              className={`purpose-chip p-4 rounded-xl text-left relative ${
                isActive ? "active" : ""
              }`}
              style={
                isActive
                  ? {
                      boxShadow: `0 8px 32px -8px ${p.activeGlow}`,
                      borderColor: `${p.iconColor}33`,
                    }
                  : undefined
              }
            >
              <motion.div
                animate={isActive ? { scale: [1, 1.15, 1] } : { scale: 1 }}
                transition={{ duration: 0.4 }}
              >
                <p.icon
                  className="w-5 h-5 mb-3 transition-colors duration-300"
                  style={{ color: isActive ? p.iconColor : "#4b5563" }}
                />
              </motion.div>
              <p
                className="text-[13px] font-semibold transition-colors duration-300"
                style={{ color: isActive ? p.iconColor : "#d1d5db" }}
              >
                {p.label}
              </p>
              <p className="text-[11px] text-gray-600 mt-1 leading-relaxed">
                {p.description}
              </p>

              {isActive && (
                <motion.div
                  layoutId="activeDot"
                  className="absolute top-3 right-3 w-1.5 h-1.5 rounded-full"
                  style={{ background: p.iconColor }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
            </motion.button>
          );
        })}
      </div>

      <AnimatePresence>
        {purpose === "custom" && (
          <motion.div
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: "auto", marginTop: 12 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="relative">
              <textarea
                value={customPrompt}
                onChange={(e) => onCustomPromptChange(e.target.value)}
                placeholder="E.g. Create a persuasive investor pitch deck with focus on market opportunity and financials..."
                className="w-full bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 text-sm text-gray-300 placeholder-gray-700 resize-none focus:outline-none focus:border-indigo-500/30 focus:bg-white/[0.03] transition-all duration-300"
                rows={3}
              />
              <div className="absolute bottom-3 right-3 text-[10px] text-gray-700">
                {customPrompt.length}/500
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
