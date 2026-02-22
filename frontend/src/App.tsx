import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Download,
  Zap,
  FileText,
  Layers,
  Upload,
  HelpCircle,
  Loader2,
} from "lucide-react";
import axios from "axios";
import TemplateGallery from "./components/TemplateGallery";
import PromptEditor from "./components/PromptEditor";
import ProgressIndicator from "./components/ProgressIndicator";
import type { Template } from "./types/template";

interface ClarifyQuestion {
  id: string;
  question: string;
  hint: string;
}

const API_URL = "";

const PURPOSES = [
  { id: "business", label: "Business", icon: "💼" },
  { id: "school", label: "Education", icon: "🎓" },
  { id: "scientific", label: "Scientific", icon: "🔬" },
] as const;

type Step = 1 | 2 | 3;

export default function App() {
  const [step, setStep] = useState<Step>(1);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [userPrompt, setUserPrompt] = useState("");
  const [purpose, setPurpose] = useState("business");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfDragging, setPdfDragging] = useState(false);
  const [promptError, setPromptError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  // Clarification flow
  const [clarifyLoading, setClarifyLoading] = useState(false);
  const [clarifyQuestions, setClarifyQuestions] = useState<ClarifyQuestion[] | null>(null);
  const [clarifyAnswers, setClarifyAnswers] = useState<Record<string, string>>({});

  // ── Navigation ──────────────────────────────────────────
  const goStep2 = () => {
    if (!selectedTemplate) return;
    setStep(2);
  };

  const goStep3 = async () => {
    if (userPrompt.trim().length < 10) {
      setPromptError(true);
      return;
    }
    setPromptError(false);
    setClarifyQuestions(null);
    setClarifyAnswers({});

    setClarifyLoading(true);
    try {
      const fd = new FormData();
      fd.append("user_prompt", userPrompt);
      fd.append("purpose", purpose);
      if (pdfFile) fd.append("pdf_file", pdfFile);

      const res = await axios.post(`${API_URL}/api/clarify`, fd, { timeout: 30000 });
      const { needs_clarification, questions } = res.data;

      if (needs_clarification && questions?.length > 0) {
        setClarifyQuestions(questions);
      } else {
        setStep(3);
      }
    } catch {
      // If clarify check fails, proceed directly to step 3
      setStep(3);
    } finally {
      setClarifyLoading(false);
    }
  };

  const proceedWithAnswers = () => {
    setClarifyQuestions(null);
    setStep(3);
  };

  const handleReset = () => {
    setStep(1);
    setSelectedTemplate(null);
    setUserPrompt("");
    setPurpose("business");
    setPdfFile(null);
    setDone(false);
    setError("");
    setPromptError(false);
    setClarifyQuestions(null);
    setClarifyAnswers({});
  };

  // ── Document drag & drop (PDF or Markdown) ───────────────
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setPdfDragging(false);
    const file = e.dataTransfer.files?.[0];
    const name = file?.name.toLowerCase() ?? "";
    if (name.endsWith(".pdf") || name.endsWith(".md")) setPdfFile(file);
  };

  // ── Generate ─────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!selectedTemplate || userPrompt.trim().length < 10) return;
    setLoading(true);
    setError("");
    setDone(false);

    const formData = new FormData();
    formData.append("template_id", selectedTemplate.id);
    formData.append("user_prompt", userPrompt);
    formData.append("purpose", purpose);
    if (pdfFile) formData.append("pdf_file", pdfFile);
    const filledAnswers = Object.fromEntries(
      Object.entries(clarifyAnswers).filter(([, v]) => v.trim())
    );
    if (Object.keys(filledAnswers).length > 0) {
      formData.append("clarifications", JSON.stringify(filledAnswers));
    }

    try {
      const response = await axios.post(`${API_URL}/api/generate`, formData, {
        timeout: 180000,
      });

      const { download_id, filename } = response.data;

      // Navigate directly to the download URL — works in all browsers incl. Safari.
      // The server sets Content-Disposition: attachment so the browser downloads
      // the file without leaving the page.
      const link = document.createElement("a");
      link.href = `/api/download/${download_id}`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();

      setDone(true);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        try {
          const text = await (err.response.data as Blob).text();
          const json = JSON.parse(text);
          setError(json.detail || "Something went wrong.");
        } catch {
          setError("Something went wrong. Please try again.");
        }
      } else {
        setError("Could not connect to the server. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  };

  // ── Step indicators ───────────────────────────────────────
  const steps = [
    { n: 1, label: "Template" },
    { n: 2, label: "Content" },
    { n: 3, label: "Generate" },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-12">
      <div className="w-full max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-10"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15, duration: 0.5 }}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/[0.06] border border-indigo-500/[0.12] mb-5"
          >
            <Zap className="w-3 h-3 text-indigo-400" />
            <span className="text-[11px] font-medium tracking-wide text-indigo-400/90 uppercase">
              AI-Powered Generator
            </span>
          </motion.div>

          <h1 className="text-[42px] md:text-[52px] font-bold leading-none tracking-tight mb-3">
            <span className="bg-gradient-to-b from-white via-gray-200 to-gray-500 bg-clip-text text-transparent">
              Deck
            </span>
            <span className="bg-gradient-to-b from-indigo-300 to-indigo-500 bg-clip-text text-transparent">
              Forge
            </span>
          </h1>
          <p className="text-gray-600 text-[15px] font-light">
            Pick a template. Describe your deck. Download in seconds.
          </p>
        </motion.div>

        {/* Step progress bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex items-center justify-center gap-3 mb-8"
        >
          {steps.map(({ n, label }, i) => (
            <div key={n} className="flex items-center gap-3">
              <div className="flex flex-col items-center gap-1">
                <div
                  className={`step-dot ${
                    step === n
                      ? "step-dot-active"
                      : step > n
                      ? "step-dot-done"
                      : "step-dot-idle"
                  }`}
                >
                  {step > n ? <CheckCircle2 className="w-3 h-3" /> : n}
                </div>
                <span
                  className={`text-[10px] font-medium tracking-wide ${
                    step === n ? "text-indigo-400" : "text-gray-600"
                  }`}
                >
                  {label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div
                  className={`step-connector ${step > n ? "step-connector-done" : ""}`}
                />
              )}
            </div>
          ))}
        </motion.div>

        {/* Main card */}
        <AnimatePresence mode="wait">
          {/* ─── STEP 1 – Template Gallery ──────────────────── */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: -24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -24 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="glass-card rounded-[24px] p-7 space-y-6"
            >
              <div className="flex items-center gap-2.5">
                <span className="step-label-badge step-label-indigo">1</span>
                <span className="text-[13px] font-medium text-gray-400">
                  Choose a Template
                </span>
                {selectedTemplate && (
                  <span className="ml-auto text-xs text-indigo-400 font-medium">
                    {selectedTemplate.name} selected
                  </span>
                )}
              </div>

              <TemplateGallery
                selected={selectedTemplate}
                onSelect={setSelectedTemplate}
              />

              <div className="flex justify-end pt-2">
                <button
                  onClick={goStep2}
                  disabled={!selectedTemplate}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                    selectedTemplate
                      ? "bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-500/15"
                      : "bg-white/[0.03] text-gray-600 border border-white/[0.05] cursor-not-allowed"
                  }`}
                >
                  Next: Add Content
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* ─── STEP 2 – Prompt & Content ──────────────────── */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 24 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="glass-card rounded-[24px] p-7 space-y-6"
            >
              {/* Selected template summary */}
              {selectedTemplate && (
                <div
                  className="flex items-center gap-3 p-3 rounded-xl border"
                  style={{
                    borderColor: selectedTemplate.colors.accent + "33",
                    background: selectedTemplate.colors.accent + "0A",
                  }}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex-shrink-0"
                    style={{ background: selectedTemplate.colors.bg, border: `1.5px solid ${selectedTemplate.colors.accent}44` }}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-200">{selectedTemplate.name}</p>
                    <p className="text-xs text-gray-600">{selectedTemplate.category}</p>
                  </div>
                  <button
                    onClick={() => setStep(1)}
                    className="ml-auto text-xs text-gray-600 hover:text-gray-400 transition-colors"
                  >
                    Change
                  </button>
                </div>
              )}

              {/* Prompt */}
              <div>
                <div className="flex items-center gap-2.5 mb-3">
                  <span className="step-label-badge step-label-violet">2</span>
                  <span className="text-[13px] font-medium text-gray-400">
                    Describe Your Presentation
                  </span>
                  <span className="ml-1 text-[10px] font-medium px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/20 text-red-400">
                    required
                  </span>
                </div>
                <PromptEditor
                  value={userPrompt}
                  onChange={(v) => {
                    setUserPrompt(v);
                    if (v.trim().length >= 10) setPromptError(false);
                  }}
                  template={selectedTemplate}
                  error={promptError}
                />
              </div>

              <div className="h-px bg-gradient-to-r from-transparent via-white/[0.04] to-transparent" />

              {/* Purpose */}
              <div>
                <div className="flex items-center gap-2.5 mb-3">
                  <Layers className="w-3.5 h-3.5 text-gray-600" />
                  <span className="text-[13px] font-medium text-gray-500">
                    Presentation Style
                  </span>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {PURPOSES.map(({ id, label, icon }) => (
                    <button
                      key={id}
                      onClick={() => setPurpose(id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                        purpose === id
                          ? "bg-indigo-500/15 border-indigo-500/30 text-indigo-300"
                          : "bg-white/[0.02] border-white/[0.05] text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]"
                      }`}
                    >
                      <span>{icon}</span>
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="h-px bg-gradient-to-r from-transparent via-white/[0.04] to-transparent" />

              {/* PDF upload (optional) */}
              <div>
                <div className="flex items-center gap-2.5 mb-3">
                  <FileText className="w-3.5 h-3.5 text-gray-600" />
                  <span className="text-[13px] font-medium text-gray-500">
                    Source Document
                  </span>
                  <span className="text-[10px] text-gray-700 ml-1">optional</span>
                  <span className="ml-auto text-[10px] text-gray-700 font-mono">.pdf · .md</span>
                </div>
                <div
                  onDragOver={(e) => { e.preventDefault(); setPdfDragging(true); }}
                  onDragLeave={() => setPdfDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => {
                    if (!pdfFile) {
                      const input = document.createElement("input");
                      input.type = "file";
                      input.accept = ".pdf,.md";
                      input.onchange = (e) => {
                        const f = (e.target as HTMLInputElement).files?.[0];
                        if (f) setPdfFile(f);
                      };
                      input.click();
                    }
                  }}
                  className={`pdf-dropzone ${pdfDragging ? "dragging" : ""} ${pdfFile ? "has-file" : ""}`}
                >
                  {pdfFile ? (
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <span className="text-sm text-gray-300 truncate">{pdfFile.name}</span>
                      <button
                        onClick={(e) => { e.stopPropagation(); setPdfFile(null); }}
                        className="ml-auto text-xs text-gray-600 hover:text-red-400 transition-colors flex-shrink-0"
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-gray-600">
                      <Upload className="w-4 h-4" />
                      <span className="text-sm">
                        Drop a PDF or Markdown file here, or{" "}
                        <span className="text-gray-500 underline underline-offset-2 cursor-pointer">
                          browse
                        </span>
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Clarification questions panel */}
              <AnimatePresence>
                {clarifyQuestions && (
                  <motion.div
                    key="clarify-panel"
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                    className="space-y-4 p-4 rounded-xl border border-amber-500/20 bg-amber-500/[0.04]"
                  >
                    <div className="flex items-center gap-2">
                      <HelpCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                      <span className="text-sm font-medium text-amber-300">
                        Ein paar kurze Fragen für eine bessere Präsentation
                      </span>
                    </div>
                    <div className="space-y-3">
                      {clarifyQuestions.map((q) => (
                        <div key={q.id} className="space-y-1.5">
                          <label className="text-xs font-medium text-gray-400">
                            {q.question}
                          </label>
                          <input
                            type="text"
                            placeholder={q.hint}
                            value={clarifyAnswers[q.question] ?? ""}
                            onChange={(e) =>
                              setClarifyAnswers((prev) => ({
                                ...prev,
                                [q.question]: e.target.value,
                              }))
                            }
                            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-amber-500/40 focus:bg-white/[0.06] transition-all"
                          />
                        </div>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => { setClarifyQuestions(null); setStep(3); }}
                        className="flex-1 py-2 rounded-xl text-xs font-medium text-gray-500 hover:text-gray-300 bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-all"
                      >
                        Überspringen
                      </button>
                      <button
                        onClick={proceedWithAnswers}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white transition-all"
                      >
                        Antworten & Weiter
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Navigation */}
              {!clarifyQuestions && (
                <div className="flex items-center justify-between pt-2">
                  <button
                    onClick={() => setStep(1)}
                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm text-gray-500 hover:text-gray-300 bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-all"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                  </button>
                  <button
                    onClick={goStep3}
                    disabled={clarifyLoading}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-500/15 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {clarifyLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Checking…
                      </>
                    ) : (
                      <>
                        Review & Generate
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              )}
            </motion.div>
          )}

          {/* ─── STEP 3 – Generate ──────────────────────────── */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 24 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="glass-card rounded-[24px] p-7 space-y-6"
            >
              <div className="flex items-center gap-2.5">
                <span className="step-label-badge step-label-emerald">3</span>
                <span className="text-[13px] font-medium text-gray-400">
                  Review & Generate
                </span>
              </div>

              {/* Summary */}
              <div className="space-y-3">
                {/* Template row */}
                <div className="summary-row">
                  <span className="summary-label">Template</span>
                  <div className="flex items-center gap-2">
                    {selectedTemplate && (
                      <div
                        className="w-4 h-4 rounded flex-shrink-0"
                        style={{
                          background: selectedTemplate.colors.bg,
                          border: `1px solid ${selectedTemplate.colors.accent}66`,
                        }}
                      />
                    )}
                    <span className="summary-value">{selectedTemplate?.name}</span>
                  </div>
                </div>

                {/* Style row */}
                <div className="summary-row">
                  <span className="summary-label">Style</span>
                  <span className="summary-value capitalize">
                    {PURPOSES.find((p) => p.id === purpose)?.label ?? purpose}
                  </span>
                </div>

                {/* Document row */}
                <div className="summary-row">
                  <span className="summary-label">Source Doc</span>
                  <span className="summary-value">
                    {pdfFile ? pdfFile.name : <span className="text-gray-600">None (prompt only)</span>}
                  </span>
                </div>

                {/* Prompt row */}
                <div className="summary-row items-start">
                  <span className="summary-label mt-0.5">Prompt</span>
                  <p className="summary-value text-right max-w-xs leading-relaxed">
                    {userPrompt}
                  </p>
                </div>

                {/* Clarifications row */}
                {Object.values(clarifyAnswers).some((v) => v.trim()) && (
                  <div className="summary-row">
                    <span className="summary-label">Clarifications</span>
                    <span className="summary-value text-amber-400">
                      {Object.values(clarifyAnswers).filter((v) => v.trim()).length} answer
                      {Object.values(clarifyAnswers).filter((v) => v.trim()).length !== 1 ? "s" : ""} provided
                    </span>
                  </div>
                )}
              </div>

              <div className="h-px bg-gradient-to-r from-transparent via-white/[0.04] to-transparent" />

              {/* Generate / Progress / Done */}
              <AnimatePresence mode="wait">
                {loading ? (
                  <ProgressIndicator key="progress" />
                ) : done ? (
                  <motion.div
                    key="done"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-3"
                  >
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/[0.06] border border-emerald-500/[0.12]">
                      <div className="p-2 rounded-lg bg-emerald-500/10">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-emerald-300">
                          Presentation ready!
                        </p>
                        <p className="text-xs text-emerald-500/60 mt-0.5">
                          Your file has been downloaded
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        onClick={handleGenerate}
                        className="flex items-center justify-center gap-2 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm font-medium text-gray-400 hover:bg-white/[0.05] hover:text-gray-300 transition-all"
                      >
                        <Download className="w-4 h-4" />
                        Download Again
                      </button>
                      <button
                        onClick={handleReset}
                        className="flex items-center justify-center gap-2 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm font-medium text-gray-400 hover:bg-white/[0.05] hover:text-gray-300 transition-all"
                      >
                        <Sparkles className="w-4 h-4" />
                        New Project
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.button
                    key="button"
                    onClick={handleGenerate}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    whileHover={{ scale: 1.01, y: -1 }}
                    whileTap={{ scale: 0.99 }}
                    className="btn-generate w-full py-3.5 rounded-xl font-semibold text-[15px] bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 hover:from-indigo-500 hover:via-indigo-400 hover:to-violet-500 text-white shadow-lg shadow-indigo-500/15 transition-all duration-300"
                  >
                    <span className="flex items-center justify-center gap-2.5">
                      <Sparkles className="w-[18px] h-[18px] text-indigo-200" />
                      Generate Presentation
                    </span>
                  </motion.button>
                )}
              </AnimatePresence>

              {/* Error */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="flex items-start gap-3 p-4 rounded-xl bg-red-500/[0.06] border border-red-500/[0.12]"
                  >
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-red-300">Generation failed</p>
                      <p className="text-xs text-red-400/60 mt-1">{error}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Back button */}
              {!loading && !done && (
                <button
                  onClick={() => setStep(2)}
                  className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-400 transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Back to Content
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="flex items-center justify-center gap-2 mt-8"
        >
          <div className="h-px w-8 bg-gradient-to-r from-transparent to-white/[0.06]" />
          <span className="text-[11px] text-gray-700 tracking-wide">
            Powered by OpenAI
          </span>
          <div className="h-px w-8 bg-gradient-to-l from-transparent to-white/[0.06]" />
        </motion.div>
      </div>
    </div>
  );
}
