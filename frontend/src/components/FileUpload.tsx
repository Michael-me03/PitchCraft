import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, FileSpreadsheet, X, CheckCircle2 } from "lucide-react";

interface FileUploadProps {
  label: string;
  sublabel: string;
  accept: string;
  icon: "pdf" | "pptx";
  file: File | null;
  onFileSelect: (file: File | null) => void;
  delay?: number;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUpload({
  label,
  sublabel,
  accept,
  icon,
  file,
  onFileSelect,
  delay = 0,
}: FileUploadProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) onFileSelect(dropped);
    },
    [onFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleClick = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = accept;
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files?.[0]) onFileSelect(target.files[0]);
    };
    input.click();
  };

  const IconComponent = icon === "pdf" ? FileText : FileSpreadsheet;
  const accentColor = icon === "pdf" ? "indigo" : "violet";

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`dropzone rounded-2xl p-6 cursor-pointer relative ${
        dragging ? "dragging" : ""
      } ${file ? "has-file" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
    >
      <AnimatePresence mode="wait">
        {file ? (
          <motion.div
            key="file"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3 }}
            className="relative z-10"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatSize(file.size)}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFileSelect(null);
                }}
                className="p-1.5 rounded-lg hover:bg-white/5 transition-colors group"
              >
                <X className="w-4 h-4 text-gray-600 group-hover:text-gray-400 transition-colors" />
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="text-center relative z-10 py-3"
          >
            <div className="flex justify-center mb-4">
              <motion.div
                whileHover={{ scale: 1.05, rotate: 3 }}
                className={`p-3.5 rounded-2xl bg-${accentColor}-500/8 border border-${accentColor}-500/10`}
                style={{
                  background: `rgba(99, 102, 241, ${icon === "pdf" ? "0.06" : "0.04"})`,
                  borderColor: `rgba(${icon === "pdf" ? "99, 102, 241" : "139, 92, 246"}, 0.1)`,
                }}
              >
                <IconComponent
                  className="w-7 h-7"
                  style={{
                    color: icon === "pdf" ? "#818cf8" : "#a78bfa",
                  }}
                />
              </motion.div>
            </div>
            <p className="text-sm font-medium text-gray-300 mb-1">{label}</p>
            <p className="text-xs text-gray-600">{sublabel}</p>
            <div className="flex items-center justify-center gap-1.5 mt-3">
              <Upload className="w-3 h-3 text-gray-600" />
              <span className="text-[11px] text-gray-600 tracking-wide uppercase">
                Drop file or browse
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
