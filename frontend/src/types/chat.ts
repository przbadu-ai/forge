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
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface SSETokenEvent {
  type: "token";
  delta: string;
}
export interface SSEDoneEvent {
  type: "done";
  message_id: number;
}
export interface SSEErrorEvent {
  type: "error";
  message: string;
}
export interface SSEStoppedEvent {
  type: "stopped";
  message_id: number;
}
export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent | SSEStoppedEvent;
