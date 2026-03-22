export interface Conversation {
  id: number;
  title: string;
  user_id: number;
  system_prompt: string | null;
  temperature: number | null;
  max_tokens: number | null;
  created_at: string;
  updated_at: string;
}

export interface GeneralSettings {
  system_prompt: string | null;
  temperature: number;
  max_tokens: number;
  skill_directories: string[];
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  trace_data: string | null;
  sources?: SourceCitationData[] | null;
  created_at: string;
}

export interface TraceEvent {
  id: string;
  type: "run_start" | "run_end" | "token_generation" | "error";
  name: string;
  status: "running" | "completed" | "error";
  started_at: string;
  completed_at: string | null;
  input?: unknown;
  output?: unknown;
  error?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface SSETokenEvent {
  type: "token";
  delta: string;
}
export interface SourceCitationData {
  file_name: string;
  chunk_text: string;
  score: number;
}

export interface SSEDoneEvent {
  type: "done";
  message_id: number;
  sources?: SourceCitationData[];
}
export interface SSEErrorEvent {
  type: "error";
  message: string;
}
export interface SSEStoppedEvent {
  type: "stopped";
  message_id: number;
}
export interface SSETraceEvent {
  type: "trace_event";
  event: TraceEvent;
}
export type SSEEvent =
  | SSETokenEvent
  | SSEDoneEvent
  | SSEErrorEvent
  | SSEStoppedEvent
  | SSETraceEvent;
