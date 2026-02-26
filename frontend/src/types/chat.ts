// ============================================================================
// SECTION: Chat Message Types
// ============================================================================

export type MessageRole = "user" | "assistant" | "thinking" | "preview" | "system";

export interface FileAttachment {
  name: string;
  type: "pdf" | "md" | "pptx";
}

export interface QualityLoopEntry {
  attempt: number;
  verdict: string;
  reasoning: string;
  issues: string[];
}

export interface QualityReport {
  attempts: number;
  final_verdict: string;
  history: QualityLoopEntry[];
}

export interface PreviewData {
  downloadId: string;
  filename: string;
  totalSlides: number;
}

export interface ClarifyQuestion {
  id: string;
  question: string;
  hint: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  thinkingData?: QualityLoopEntry;
  previewData?: PreviewData;
  attachments?: FileAttachment[];
  clarifyQuestions?: ClarifyQuestion[];
}

// ============================================================================
// SECTION: Chat Session
// ============================================================================

export interface SessionSettings {
  templateId: string | null;
  templateName: string | null;
  purpose: string;
  language: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
  settings: SessionSettings;
  lastDownloadId?: string;
  lastFilename?: string;
}

// ============================================================================
// SECTION: Generation State
// ============================================================================

export type GenerationPhase =
  | "idle"
  | "clarifying"
  | "generating"
  | "rendering"
  | "converting"
  | "done"
  | "error";
