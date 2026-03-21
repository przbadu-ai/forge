export interface Conversation {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string;
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
export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent;
