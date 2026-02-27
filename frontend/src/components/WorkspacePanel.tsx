// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Globe,
  Layers,
  Upload,
  FileText,
  X,
  Presentation,
  Send,
  Loader2,
  ArrowLeft,
  Sparkles,
} from "lucide-react";
import type { PreviewData, SessionSettings, GenerationPhase } from "../types/chat";
import type { Template } from "../types/template";
import TemplateGallery from "./TemplateGallery";
import GenerationProgress from "./GenerationProgress";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  preview: PreviewData | null;
  settings: SessionSettings;
  selectedTemplate: Template | null;
  customFile: File | null;
  pdfFile: File | null;
  phase: GenerationPhase;
  onSelectTemplate: (t: Template) => void;
  onUploadTemplate: (f: File) => void;
  onUploadPdf: (f: File | null) => void;
  onSettingsChange: (s: Partial<SessionSettings>) => void;
  onGenerate: (prompt: string, file?: File) => void;
  onCancel: () => void;
  onBackToSetup: () => void;
}

// ============================================================================
// SECTION: Constants
// ============================================================================

const STARTERS = [
  "Create a Q3 investor update with revenue charts and KPIs",
  "Build a pitch deck for an AI startup raising Series A",
  "Make a scientific presentation about climate change data",
  "Design a school presentation about the solar system",
];

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

export default function WorkspacePanel({
  preview,
  settings,
  selectedTemplate,
  customFile,
  pdfFile,
  phase,
  onSelectTemplate,
  onUploadTemplate,
  onUploadPdf,
  onSettingsChange,
  onGenerate,
  onCancel,
  onBackToSetup,
}: Props) {
  const [prompt, setPrompt] = useState("");
  const [currentSlide, setCurrentSlide] = useState(0);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [slideLoading, setSlideLoading] = useState(false);
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isGenerating =
    phase === "generating" || phase === "converting" || phase === "clarifying" || phase === "rendering";

  // ── Reset slide on new preview ──────────────────────────────────────────
  useEffect(() => {
    setCurrentSlide(0);
  }, [preview?.downloadId]);

  // ── Load slide image ───────────────────────────────────────────────────
  useEffect(() => {
    if (!preview || preview.totalSlides === 0) {
      setImageUrl(null);
      return;
    }
    setSlideLoading(true);
    const url = `/api/preview/${preview.downloadId}/slide/${currentSlide}`;
    const img = new Image();
    img.onload = () => {
      setImageUrl(url);
      setSlideLoading(false);
    };
    img.onerror = () => {
      setImageUrl(null);
      setSlideLoading(false);
    };
    img.src = url;
  }, [preview, currentSlide]);

  // ── Keyboard nav for slides ────────────────────────────────────────────
  useEffect(() => {
    if (!preview || preview.totalSlides === 0) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
      if (e.key === "ArrowLeft") setCurrentSlide((p) => Math.max(0, p - 1));
      if (e.key === "ArrowRight") setCurrentSlide((p) => Math.min(preview.totalSlides - 1, p + 1));
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [preview]);

  // ── Send prompt ────────────────────────────────────────────────────────
  const handleSend = useCallback(() => {
    const trimmed = prompt.trim();
    if (!trimmed) return;
    onGenerate(trimmed);
    setPrompt("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [prompt, onGenerate]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleTextInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    if (val.length <= 2000) setPrompt(val);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
    }
  }, []);

  // ── Generating state → show progress in center ─────────────────────────
  if (isGenerating && !preview) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-[#060609]">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 flex items-center justify-center mb-6">
          <Sparkles className="w-8 h-8 text-indigo-400" />
        </div>
        <h2 className="text-lg font-semibold text-white/80 mb-4">Creating your presentation...</h2>
        <GenerationProgress phase={phase} />
        <button
          onClick={onCancel}
          className="mt-6 px-4 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-xs text-white/40 hover:text-white/70 transition-colors"
        >
          Cancel
        </button>
      </div>
    );
  }

  // ── Preview mode (slides generated) ────────────────────────────────────
  if (preview) {
    return (
      <div className="h-full flex flex-col bg-[#060609]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToSetup}
              className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"
              title="Back to setup"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <Presentation className="w-4 h-4 text-indigo-400" />
            <span className="text-sm text-white/60 truncate max-w-[300px]">
              {preview.filename}
            </span>
          </div>
          <a
            href={`/api/download/${preview.downloadId}`}
            download={preview.filename}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Download PPTX
          </a>
        </div>

        {/* Slide viewer */}
        <div className="flex-1 flex items-center justify-center p-6 overflow-hidden">
          {isGenerating ? (
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
              </div>
              <p className="text-sm text-white/40">Updating presentation...</p>
            </div>
          ) : (
            <motion.div
              key={`${preview.downloadId}-${currentSlide}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="relative w-full max-w-4xl"
              style={{ aspectRatio: "16/9" }}
            >
              {slideLoading ? (
                <div className="absolute inset-0 flex items-center justify-center bg-white/[0.02] rounded-xl">
                  <div className="w-8 h-8 border-2 border-white/10 border-t-indigo-400 rounded-full animate-spin" />
                </div>
              ) : imageUrl ? (
                <img
                  src={imageUrl}
                  alt={`Slide ${currentSlide + 1}`}
                  className="w-full h-full object-contain rounded-xl shadow-2xl shadow-black/50"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-white/[0.02] rounded-xl">
                  <p className="text-sm text-white/20">Preview not available</p>
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Slide navigation */}
        {preview.totalSlides > 0 && !isGenerating && (
          <div className="flex items-center justify-center gap-4 px-4 py-3 border-t border-white/[0.06]">
            <button
              onClick={() => setCurrentSlide((p) => Math.max(0, p - 1))}
              disabled={currentSlide === 0}
              className="p-2 rounded-lg hover:bg-white/[0.06] text-white/40 hover:text-white/70 transition-colors disabled:opacity-20"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-1.5">
              {Array.from({ length: Math.min(preview.totalSlides, 20) }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentSlide(i)}
                  className={`transition-all rounded-full ${
                    i === currentSlide
                      ? "bg-indigo-400 w-4 h-2"
                      : "bg-white/15 hover:bg-white/30 w-2 h-2"
                  }`}
                />
              ))}
              {preview.totalSlides > 20 && (
                <span className="text-[10px] text-white/20 ml-1">+{preview.totalSlides - 20}</span>
              )}
            </div>

            <span className="text-xs text-white/40 min-w-[60px] text-center">
              {currentSlide + 1} / {preview.totalSlides}
            </span>

            <button
              onClick={() => setCurrentSlide((p) => Math.min(preview.totalSlides - 1, p + 1))}
              disabled={currentSlide >= preview.totalSlides - 1}
              className="p-2 rounded-lg hover:bg-white/[0.06] text-white/40 hover:text-white/70 transition-colors disabled:opacity-20"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    );
  }

  // ── Setup mode (template selection + upload + prompt) ──────────────────
  return (
    <div className="h-full flex flex-col bg-[#060609]">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">
          {/* Header */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-3">
              <PitchCraftLogo />
              <h1 className="text-2xl font-bold text-white/90">PitchCraft</h1>
            </div>
            <p className="text-sm text-white/40">
              Configure your presentation settings, then describe what you need.
            </p>
          </div>

          {/* ── Language & Style row ────────────────────────────────── */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2.5">
                <Globe className="w-4 h-4 text-white/30" />
                <span className="text-xs font-medium text-white/50">Language</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.id}
                    onClick={() => onSettingsChange({ language: lang.id })}
                    className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
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
            <div>
              <div className="flex items-center gap-2 mb-2.5">
                <Layers className="w-4 h-4 text-white/30" />
                <span className="text-xs font-medium text-white/50">Style</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {PURPOSES.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => onSettingsChange({ purpose: p.id })}
                    className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
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
          </div>

          {/* ── Source Document Upload ──────────────────────────────── */}
          <div>
            <div className="flex items-center gap-2 mb-2.5">
              <FileText className="w-4 h-4 text-white/30" />
              <span className="text-xs font-medium text-white/50">Source Document</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold uppercase tracking-wider ml-1">
                Recommended
              </span>
            </div>
            {pdfFile ? (
              <div className="flex items-center gap-3 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                <FileText className="w-5 h-5 text-indigo-400" />
                <span className="text-sm text-indigo-300 flex-1 truncate">{pdfFile.name}</span>
                <button
                  onClick={() => onUploadPdf(null)}
                  className="text-white/30 hover:text-red-400 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => pdfInputRef.current?.click()}
                className="w-full p-4 rounded-xl border border-dashed border-white/[0.1] hover:border-indigo-500/30 hover:bg-indigo-500/5 text-sm text-white/30 hover:text-white/50 transition-all flex items-center justify-center gap-2"
              >
                <Upload className="w-4 h-4" />
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
            <div className="flex items-center gap-2 mb-2.5">
              <Presentation className="w-4 h-4 text-white/30" />
              <span className="text-xs font-medium text-white/50">Template</span>
              {selectedTemplate && (
                <span className="ml-auto text-xs text-indigo-400">{selectedTemplate.name}</span>
              )}
            </div>
            <TemplateGallery
              selected={selectedTemplate}
              onSelect={onSelectTemplate}
              onUpload={onUploadTemplate}
              customFile={customFile}
            />
          </div>
        </div>
      </div>

      {/* ── Prompt input bar (sticky bottom) ───────────────────────────── */}
      <div className="border-t border-white/[0.06] bg-[#0a0a12]/90 backdrop-blur-xl px-4 py-3">
        {/* Starter prompts */}
        {!prompt && (
          <div className="max-w-3xl mx-auto flex flex-wrap gap-2 mb-2">
            {STARTERS.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setPrompt(s);
                  textareaRef.current?.focus();
                }}
                className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-[11px] text-white/40 hover:text-white/70 hover:bg-white/[0.06] hover:border-white/[0.1] transition-all"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <div className="max-w-3xl mx-auto flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={handleTextInput}
            onKeyDown={handleKeyDown}
            placeholder="Describe the presentation you want to create..."
            disabled={isGenerating}
            rows={1}
            className="flex-1 resize-none bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white/90 placeholder-white/25 focus:outline-none focus:border-indigo-500/40 transition-colors disabled:opacity-40"
            style={{ minHeight: "42px", maxHeight: "120px" }}
          />
          {isGenerating ? (
            <button
              onClick={onCancel}
              className="p-2.5 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors"
              title="Cancel"
            >
              <X className="w-4.5 h-4.5" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!prompt.trim() || !selectedTemplate}
              className="p-2.5 rounded-xl bg-indigo-600/80 hover:bg-indigo-600 text-white transition-colors disabled:opacity-30"
              title="Generate presentation"
            >
              <Send className="w-4.5 h-4.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// SECTION: Logo Component
// ============================================================================

function PitchCraftLogo() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Back slide */}
      <rect x="6" y="4" width="22" height="15" rx="2" fill="#4338ca" opacity="0.3" />
      {/* Middle slide */}
      <rect x="8" y="8" width="22" height="15" rx="2" fill="#6366f1" opacity="0.5" />
      {/* Front slide */}
      <rect x="10" y="12" width="22" height="15" rx="2" fill="#818cf8" opacity="0.9" />
      {/* Sparkle dot */}
      <circle cx="28" cy="10" r="3" fill="#c7d2fe" />
      {/* Chart bars inside front slide */}
      <rect x="14" y="20" width="3" height="4" rx="0.5" fill="#c7d2fe" opacity="0.7" />
      <rect x="18.5" y="18" width="3" height="6" rx="0.5" fill="#c7d2fe" opacity="0.8" />
      <rect x="23" y="16" width="3" height="8" rx="0.5" fill="#c7d2fe" opacity="0.9" />
    </svg>
  );
}
