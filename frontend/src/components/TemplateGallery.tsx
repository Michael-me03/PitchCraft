import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Check, Star, Zap } from "lucide-react";
import { TEMPLATES, CATEGORIES, type Category } from "../data/templates";
import type { Template } from "../types/template";

interface Props {
  selected: Template | null;
  onSelect: (t: Template) => void;
}

export default function TemplateGallery({ selected, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<Category>("All");
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const filtered = TEMPLATES.filter((t) => {
    const matchCat = activeCategory === "All" || t.category === activeCategory;
    const q = query.toLowerCase();
    const matchQ =
      !q ||
      t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.tags.some((tag) => tag.toLowerCase().includes(q));
    return matchCat && matchQ;
  });

  const handleSelect = (t: Template) => {
    if (selected?.id === t.id) return;
    setLoadingId(t.id);
    setTimeout(() => {
      setLoadingId(null);
      onSelect(t);
    }, 1000);
  };

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search templates..."
          className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-indigo-500/40 focus:bg-white/[0.05] transition-all"
        />
      </div>

      {/* Category chips */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`category-chip px-3 py-1 rounded-full text-xs font-medium transition-all ${
              activeCategory === cat
                ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-300"
                : "bg-white/[0.03] border-white/[0.06] text-gray-500 hover:text-gray-300 hover:bg-white/[0.05]"
            } border`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="template-grid">
        <AnimatePresence mode="popLayout">
          {filtered.map((t, i) => {
            const isSelected = selected?.id === t.id;
            const isLoading = loadingId === t.id;
            const isDark =
              parseInt(t.colors.bg.slice(1, 3), 16) < 128 ||
              t.colors.bg === "#000000";

            return (
              <motion.div
                key={t.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2, delay: i * 0.03 }}
                onClick={() => handleSelect(t)}
                className={`template-card ${isSelected ? "selected" : ""}`}
              >
                {/* Mini slide preview */}
                <div
                  className="template-preview"
                  style={{ background: t.colors.bg }}
                >
                  {isLoading ? (
                    <div className="shimmer-overlay" />
                  ) : (
                    <>
                      {/* Fake title bar */}
                      <div
                        className="fake-title-bar"
                        style={{ background: t.colors.accent + "33" }}
                      >
                        <div
                          className="fake-title-line"
                          style={{ background: t.colors.accent }}
                        />
                        <div
                          className="fake-title-line-sm"
                          style={{ background: t.colors.muted }}
                        />
                      </div>
                      {/* Fake content lines */}
                      <div className="fake-content">
                        {[0.7, 0.5, 0.6, 0.4].map((w, j) => (
                          <div
                            key={j}
                            className="fake-line"
                            style={{
                              width: `${w * 100}%`,
                              background: isDark
                                ? "rgba(255,255,255,0.12)"
                                : "rgba(0,0,0,0.12)",
                            }}
                          />
                        ))}
                      </div>
                      {/* Fake chart block */}
                      <div
                        className="fake-chart"
                        style={{
                          borderColor: t.colors.accent + "44",
                          background: t.colors.accent + "11",
                        }}
                      >
                        <div className="fake-bars">
                          {[0.6, 0.9, 0.5, 0.75, 0.4].map((h, j) => (
                            <div
                              key={j}
                              className="fake-bar"
                              style={{
                                height: `${h * 100}%`,
                                background: t.colors.accent,
                                opacity: 0.6 + j * 0.08,
                              }}
                            />
                          ))}
                        </div>
                      </div>
                    </>
                  )}

                  {/* Selected overlay */}
                  {isSelected && (
                    <div className="selected-overlay">
                      <div className="check-badge">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Card info */}
                <div className="template-info">
                  <div className="flex items-start justify-between gap-1">
                    <span className="template-name">{t.name}</span>
                    <div className="flex gap-1 flex-shrink-0">
                      {t.popular && (
                        <span className="badge badge-popular">
                          <Star className="w-2.5 h-2.5" />
                        </span>
                      )}
                      {t.new && (
                        <span className="badge badge-new">
                          <Zap className="w-2.5 h-2.5" />
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="template-category">{t.category}</span>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {filtered.length === 0 && (
          <div className="col-span-full py-8 text-center text-sm text-gray-600">
            No templates match your search.
          </div>
        )}
      </div>
    </div>
  );
}
