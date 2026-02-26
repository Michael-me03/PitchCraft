// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Settings,
  Presentation,
  Globe,
  Layers,
  Upload,
  FileText,
  X,
  PanelRightClose,
} from "lucide-react";
import type { PreviewData, SessionSettings } from "../types/chat";
import type { Template } from "../types/template";
import TemplateGallery from "./TemplateGallery";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  preview: PreviewData | null;
  onOpenSettings: () => void;
  // Settings props (shown when no preview)
  settings?: SessionSettings;
  selectedTemplate?: Template | null;
  customFile?: File | null;
  pdfFile?: File | null;
  onSelectTemplate?: (t: Template) => void;
  onUploadTemplate?: (f: File) => void;
  onUploadPdf?: (f: File | null) => void;
  onSettingsChange?: (s: Partial<SessionSettings>) => void;
  // Collapse support
  collapsed?: boolean;
  onToggle?: () => void;
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

export default function PreviewPanel({
  preview,
  onOpenSettings,
  settings,
  selectedTemplate,
  customFile,
  pdfFile,
  onSelectTemplate,
  onUploadTemplate,
  onUploadPdf,
  onSettingsChange,
  collapsed: _collapsed,
  onToggle,
}: Props) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const pdfInputRef = useRef<HTMLInputElement>(null);

  // ── Reset slide index when preview changes ─────────────────────────────
  useEffect(() => {
    setCurrentSlide(0);
  }, [preview?.downloadId]);

  // ── Load slide image ───────────────────────────────────────────────────
  useEffect(() => {
    if (!preview || preview.totalSlides === 0) {
      setImageUrl(null);
      return;
    }
    setLoading(true);
    const url = `/api/preview/${preview.downloadId}/slide/${currentSlide}`;
    const img = new Image();
    img.onload = () => {
      setImageUrl(url);
      setLoading(false);
    };
    img.onerror = () => {
      setImageUrl(null);
      setLoading(false);
    };
    img.src = url;
  }, [preview, currentSlide]);

  // ── Keyboard navigation ────────────────────────────────────────────────
  useEffect(() => {
    if (!preview || preview.totalSlides === 0) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        setCurrentSlide((p) => Math.max(0, p - 1));
      } else if (e.key === "ArrowRight") {
        setCurrentSlide((p) => Math.min(preview.totalSlides - 1, p + 1));
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [preview]);

  // ── No preview → Show inline settings with template gallery ────────────
  if (!preview) {
    return (
      <div className="h-full flex flex-col bg-[#07070d] border-l border-white/[0.06]">
        {/* Header */}
        <div className="flex items-center gap-2 p-3 border-b border-white/[0.06]">
          <Settings className="w-4 h-4 text-white/30" />
          <span className="text-xs font-medium text-white/50">Configuration</span>
        </div>

        {/* Settings content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {/* Language */}
          {settings && onSettingsChange && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Globe className="w-3.5 h-3.5 text-white/30" />
                <span className="text-xs font-medium text-white/40">Language</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.id}
                    onClick={() => onSettingsChange({ language: lang.id })}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${settings.language === lang.id
                      ? "bg-indigo-600/30 border border-indigo-500/40 text-indigo-300"
                      : "bg-white/[0.04] border border-white/[0.06] text-white/50 hover:bg-white/[0.08]"
                      }`}
                  >
                    {lang.icon} {lang.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Purpose */}
          {settings && onSettingsChange && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Layers className="w-3.5 h-3.5 text-white/30" />
                <span className="text-xs font-medium text-white/40">Style</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {PURPOSES.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => onSettingsChange({ purpose: p.id })}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${settings.purpose === p.id
                      ? "bg-indigo-600/30 border border-indigo-500/40 text-indigo-300"
                      : "bg-white/[0.04] border border-white/[0.06] text-white/50 hover:bg-white/[0.08]"
                      }`}
                  >
                    {p.icon} {p.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* PDF Upload */}
          {onUploadPdf && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-3.5 h-3.5 text-white/30" />
                <span className="text-xs font-medium text-white/40">Source Document</span>
                <span className="text-[10px] text-white/20 ml-1">optional</span>
              </div>
              {pdfFile ? (
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="text-xs text-indigo-300 flex-1 truncate">{pdfFile.name}</span>
                  <button
                    onClick={() => onUploadPdf(null)}
                    className="text-white/30 hover:text-red-400 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => pdfInputRef.current?.click()}
                  className="w-full p-2.5 rounded-lg border border-dashed border-white/[0.08] hover:border-white/[0.15] text-xs text-white/25 hover:text-white/40 transition-colors flex items-center justify-center gap-2"
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
          )}

          {/* Divider */}
          <div className="h-px bg-white/[0.04]" />

          {/* Template Gallery */}
          {onSelectTemplate && onUploadTemplate && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Presentation className="w-3.5 h-3.5 text-white/30" />
                <span className="text-xs font-medium text-white/40">Template</span>
                {selectedTemplate && (
                  <span className="ml-auto text-[10px] text-indigo-400">
                    {selectedTemplate.name}
                  </span>
                )}
              </div>
              <TemplateGallery
                selected={selectedTemplate ?? null}
                onSelect={onSelectTemplate}
                onUpload={onUploadTemplate}
                customFile={customFile ?? null}
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── With preview ───────────────────────────────────────────────────────
  return (
    <div className="h-full flex flex-col bg-[#07070d] border-l border-white/[0.06]">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <Presentation className="w-4 h-4 text-white/40" />
          <span className="text-xs text-white/50 truncate max-w-[200px]">
            {preview.filename}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <a
            href={`/api/download/${preview.downloadId}`}
            download={preview.filename}
            className="p-2 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-indigo-400 transition-colors"
            title="Download PPTX"
          >
            <Download className="w-4 h-4" />
          </a>
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
          {onToggle && (
            <button
              onClick={onToggle}
              className="p-2 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"
              title="Collapse preview"
            >
              <PanelRightClose className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Slide viewer */}
      <div className="flex-1 flex items-center justify-center p-4 overflow-hidden">
        <motion.div
          key={`${preview.downloadId}-${currentSlide}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="relative w-full max-w-full"
          style={{ aspectRatio: "16/9" }}
        >
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white/[0.02] rounded-lg">
              <div className="w-6 h-6 border-2 border-white/10 border-t-indigo-400 rounded-full animate-spin" />
            </div>
          ) : imageUrl ? (
            <img
              src={imageUrl}
              alt={`Slide ${currentSlide + 1}`}
              className="w-full h-full object-contain rounded-lg shadow-2xl"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-white/[0.02] rounded-lg">
              <p className="text-xs text-white/20">Preview not available</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Navigation */}
      {preview.totalSlides > 0 && (
        <div className="flex items-center justify-center gap-4 p-3 border-t border-white/[0.06]">
          <button
            onClick={() => setCurrentSlide((p) => Math.max(0, p - 1))}
            disabled={currentSlide === 0}
            className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/40 hover:text-white/70 transition-colors disabled:opacity-20"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(preview.totalSlides, 15) }).map(
              (_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentSlide(i)}
                  className={`w-1.5 h-1.5 rounded-full transition-all ${i === currentSlide
                    ? "bg-indigo-400 w-3"
                    : "bg-white/15 hover:bg-white/30"
                    }`}
                />
              ),
            )}
            {preview.totalSlides > 15 && (
              <span className="text-[10px] text-white/20 ml-1">
                +{preview.totalSlides - 15}
              </span>
            )}
          </div>

          <span className="text-xs text-white/30 min-w-[60px] text-center">
            {currentSlide + 1} / {preview.totalSlides}
          </span>

          <button
            onClick={() =>
              setCurrentSlide((p) =>
                Math.min(preview.totalSlides - 1, p + 1),
              )
            }
            disabled={currentSlide >= preview.totalSlides - 1}
            className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/40 hover:text-white/70 transition-colors disabled:opacity-20"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
