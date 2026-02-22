import { motion, AnimatePresence } from "framer-motion";
import type { Template } from "../types/template";

const EXAMPLE_PROMPTS: Record<string, string[]> = {
  Business: [
    "Create a Q3 investor update highlighting revenue growth and market expansion",
    "Build a competitive analysis deck comparing our product to top 3 competitors",
    "Design a board presentation on our 2025 strategic roadmap",
    "Make a sales pitch deck for enterprise SaaS clients",
  ],
  Education: [
    "Explain the causes and effects of climate change with data",
    "Summarize the key findings of this research paper",
    "Create a lecture overview on machine learning fundamentals",
    "Design a lesson plan presentation on world history",
  ],
  Creative: [
    "Showcase our design portfolio with project highlights and outcomes",
    "Create a brand identity presentation for a new product launch",
    "Build a creative agency capabilities deck",
    "Design a mood board and concept presentation",
  ],
  Minimal: [
    "Create a clean overview of our company mission and values",
    "Build a simple project status update presentation",
    "Design a minimalist product introduction deck",
    "Make a concise executive briefing",
  ],
  Tech: [
    "Present the architecture of our new microservices platform",
    "Create a technical deep-dive on our AI/ML pipeline",
    "Build a developer onboarding overview for the engineering team",
    "Design a cybersecurity incident response playbook",
  ],
  default: [
    "Create a professional presentation about this topic",
    "Build a data-driven summary with key insights",
    "Design an engaging overview with charts and visuals",
  ],
};

interface Props {
  value: string;
  onChange: (v: string) => void;
  template: Template | null;
  error: boolean;
}

const MAX_CHARS = 1000;

export default function PromptEditor({ value, onChange, template, error }: Props) {
  const examples =
    (template ? EXAMPLE_PROMPTS[template.category] : null) ??
    EXAMPLE_PROMPTS.default;

  const charCount = value.length;
  const isNearLimit = charCount > MAX_CHARS * 0.8;

  return (
    <div className="space-y-3">
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => {
            if (e.target.value.length <= MAX_CHARS) onChange(e.target.value);
          }}
          placeholder={
            template
              ? `Describe what you want to present with the "${template.name}" template...`
              : "Describe what you want to present..."
          }
          rows={4}
          className={`prompt-textarea ${error ? "prompt-textarea-error" : ""}`}
        />
        <div
          className={`char-counter ${isNearLimit ? "char-counter-warn" : ""}`}
        >
          {charCount}/{MAX_CHARS}
        </div>
      </div>

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="text-xs text-red-400"
          >
            Please enter at least 10 characters to describe your presentation.
          </motion.p>
        )}
      </AnimatePresence>

      {/* Example prompt chips */}
      <div className="space-y-2">
        <p className="text-[11px] text-gray-600 uppercase tracking-wide font-medium">
          Try an example
        </p>
        <div className="flex flex-wrap gap-2">
          {examples.map((ex) => (
            <button
              key={ex}
              onClick={() => onChange(ex)}
              className="example-chip"
              title={ex}
            >
              {ex.length > 48 ? ex.slice(0, 48) + "…" : ex}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
