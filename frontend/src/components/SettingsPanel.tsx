// ============================================================================
// SECTION: Imports
// ============================================================================

import { motion } from "framer-motion";
import { X, Upload, FileText } from "lucide-react";
import { useRef } from "react";
import TemplateGallery from "./TemplateGallery";
import type { Template } from "../types/template";
import type { SessionSettings } from "../types/chat";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  settings: SessionSettings;
  selectedTemplate: Template | null;
  customFile: File | null;
  pdfFile: File | null;
  onSelectTemplate: (t: Template) => void;
  onUploadTemplate: (f: File) => void;
  onUploadPdf: (f: File | null) => void;
  onSettingsChange: (s: Partial<SessionSettings>) => void;
  onClose: () => void;
}

// ============================================================================
// SECTION: Constants
// ============================================================================

const PURPOSES = [
  { id: "business", label: "Business", icon: "💼" },
  { id: "school", label: "Education", icon: "🎓" },
  { id: "scientific", label: "Scientific", icon: "🔬" },
] as const;

const LANGUAGES = [
  { id: "de", label: "Deutsch", icon: "🇩🇪" },
  { id: "en", label: "English", icon: "🇬🇧" },
  { id: "fr", label: "Français", icon: "🇫🇷" },
  { id: "es", label: "Español", icon: "🇪🇸" },
] as const;

// ============================================================================
// SECTION: Component
// ============================================================================

export default function SettingsPanel({
  settings,
  selectedTemplate,
  customFile,
  pdfFile,
  onSelectTemplate,
  onUploadTemplate,
  onUploadPdf,
  onSettingsChange,
  onClose,
}: Props) {
  const pdfInputRef = useRef<HTMLInputElement>(null);

  return (
    <motion.div
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 300 }}
      className="fixed inset-y-0 right-0 w-[480px] max-w-full z-50 bg-[#0a0a14]/95 backdrop-blur-xl border-l border-white/[0.08] shadow-2xl flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/[0.06]">
        <h3 className="text-sm font-semibold text-white/80">Settings</h3>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* ── Language ────────────────────────────────────────────── */}
        <div>
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Language
          </label>
          <div className="flex flex-wrap gap-2">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.id}
                onClick={() => onSettingsChange({ language: lang.id })}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  settings.language === lang.id
                    ? "bg-indigo-600/30 border border-indigo-500/40 text-indigo-300"
                    : "bg-white/[0.04] border border-white/[0.06] text-white/50 hover:bg-white/[0.08]"
                }`}
              >
                {lang.icon} {lang.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Purpose ────────────────────────────────────────────── */}
        <div>
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Style
          </label>
          <div className="flex flex-wrap gap-2">
            {PURPOSES.map((p) => (
              <button
                key={p.id}
                onClick={() => onSettingsChange({ purpose: p.id })}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  settings.purpose === p.id
                    ? "bg-indigo-600/30 border border-indigo-500/40 text-indigo-300"
                    : "bg-white/[0.04] border border-white/[0.06] text-white/50 hover:bg-white/[0.08]"
                }`}
              >
                {p.icon} {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── PDF Upload ─────────────────────────────────────────── */}
        <div>
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Source Document
          </label>
          {pdfFile ? (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
              <FileText className="w-4 h-4 text-indigo-400" />
              <span className="text-xs text-indigo-300 flex-1 truncate">
                {pdfFile.name}
              </span>
              <button
                onClick={() => onUploadPdf(null)}
                className="text-white/30 hover:text-red-400 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => pdfInputRef.current?.click()}
              className="w-full p-3 rounded-lg border border-dashed border-white/[0.1] hover:border-white/[0.2] text-xs text-white/30 hover:text-white/50 transition-colors flex items-center justify-center gap-2"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload PDF or Markdown
            </button>
          )}
          <input
            ref={pdfInputRef}
            type="file"
            accept=".pdf,.md"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUploadPdf(f);
              e.target.value = "";
            }}
            className="hidden"
          />
        </div>

        {/* ── Template Gallery ────────────────────────────────────── */}
        <div>
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Template
          </label>
          <TemplateGallery
            selected={selectedTemplate}
            onSelect={onSelectTemplate}
            onUpload={onUploadTemplate}
            customFile={customFile}
          />
        </div>
      </div>
    </motion.div>
  );
}
