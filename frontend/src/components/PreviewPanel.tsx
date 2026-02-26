// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Settings,
  Presentation,
} from "lucide-react";
import type { PreviewData } from "../types/chat";

// ============================================================================
// SECTION: Props
// ============================================================================

interface Props {
  preview: PreviewData | null;
  onOpenSettings: () => void;
}

// ============================================================================
// SECTION: Component
// ============================================================================

export default function PreviewPanel({ preview, onOpenSettings }: Props) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
    // Preload image
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

  // ── No preview yet ─────────────────────────────────────────────────────
  if (!preview) {
    return (
      <div className="h-full flex flex-col bg-[#07070d] border-l border-white/[0.06]">
        {/* Settings button */}
        <div className="flex items-center justify-end p-3 border-b border-white/[0.06]">
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>

        {/* Placeholder */}
        <div className="flex-1 flex flex-col items-center justify-center px-8">
          <div className="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-4">
            <Presentation className="w-8 h-8 text-white/15" />
          </div>
          <p className="text-sm text-white/25 text-center">
            Your presentation preview will appear here
          </p>
          <p className="text-xs text-white/15 text-center mt-1">
            Send a prompt to get started
          </p>
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

          {/* Slide dots */}
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(preview.totalSlides, 15) }).map(
              (_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentSlide(i)}
                  className={`w-1.5 h-1.5 rounded-full transition-all ${
                    i === currentSlide
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
