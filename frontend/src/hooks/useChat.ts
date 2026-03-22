"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { getMessages, regenerateLastMessage } from "@/lib/chat-api";
import type { Message, SourceCitationData, SSEEvent, TraceEvent } from "@/types/chat";

import { API_BASE } from "@/lib/api";

interface UseChatOptions {
  conversationId: number | null;
  onConversationUpdated?: () => void;
}

interface UseChatReturn {
  messages: Message[];
  streamingContent: string | null;
  isStreaming: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  stopGeneration: () => void;
  regenerate: () => Promise<void>;
  messageTraces: Record<number, TraceEvent[]>;
  streamingTraceEvents: TraceEvent[];
  messageSources: Record<number, SourceCitationData[]>;
}

export function useChat({
  conversationId,
  onConversationUpdated,
}: UseChatOptions): UseChatReturn {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingTraceEvents, setStreamingTraceEvents] = useState<TraceEvent[]>([]);
  const [messageTraces, setMessageTraces] = useState<Record<number, TraceEvent[]>>({});
  const [messageSources, setMessageSources] = useState<Record<number, SourceCitationData[]>>({});
  const traceEventsRef = useRef<TraceEvent[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messageCountRef = useRef(0);

  // Load messages when conversationId changes
  useEffect(() => {
    if (!conversationId || !token) {
      setMessages([]);
      return;
    }

    let cancelled = false;
    setMessageTraces({});
    setMessageSources({});
    traceEventsRef.current = [];
    getMessages(token, conversationId)
      .then((msgs) => {
        if (!cancelled) {
          setMessages(msgs);
          messageCountRef.current = msgs.filter(
            (m) => m.role === "user",
          ).length;
          // Parse trace_data from loaded messages for replay
          const traces: Record<number, TraceEvent[]> = {};
          msgs.forEach((m) => {
            if (m.role === "assistant" && m.trace_data) {
              try {
                traces[m.id] = JSON.parse(m.trace_data) as TraceEvent[];
              } catch {
                /* skip malformed trace_data */
              }
            }
          });
          setMessageTraces(traces);

          // Restore sources from loaded messages
          const sourcesMap: Record<number, SourceCitationData[]> = {};
          msgs.forEach((m) => {
            if (m.role === "assistant" && m.sources && m.sources.length > 0) {
              sourcesMap[m.id] = m.sources;
            }
          });
          setMessageSources(sourcesMap);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load messages");
      });

    return () => {
      cancelled = true;
    };
  }, [conversationId, token]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!conversationId || !token || isStreaming) return;

      setError(null);

      // Optimistically append user message
      const optimisticUserMsg: Message = {
        id: -Date.now(),
        conversation_id: conversationId,
        role: "user",
        content,
        trace_data: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticUserMsg]);
      messageCountRef.current += 1;

      // Reset trace accumulation for new stream
      traceEventsRef.current = [];
      setStreamingTraceEvents([]);

      setIsStreaming(true);
      setStreamingContent("");

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const response = await fetch(
          `${API_BASE}/api/v1/chat/${conversationId}/stream`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ content }),
            signal: controller.signal,
            credentials: "include",
          },
        );

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || `HTTP ${response.status}`);
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE lines from buffer
          const lines = buffer.split("\n");
          // Keep last potentially incomplete line in buffer
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data: ")) continue;

            try {
              const event = JSON.parse(trimmed.slice(6)) as SSEEvent;

              if (event.type === "token") {
                accumulated += event.delta;
                setStreamingContent(accumulated);
              } else if (event.type === "trace_event") {
                traceEventsRef.current = [...traceEventsRef.current, event.event];
                setStreamingTraceEvents(traceEventsRef.current);
              } else if (event.type === "done") {
                // Capture trace snapshot before clearing
                const traceSnapshot = traceEventsRef.current;

                // Convert accumulated content into a Message
                const assistantMsg: Message = {
                  id: event.message_id,
                  conversation_id: conversationId,
                  role: "assistant",
                  content: accumulated,
                  trace_data: null,
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, assistantMsg]);
                setMessageTraces((prev) => ({ ...prev, [event.message_id]: traceSnapshot }));
                if (event.sources && event.sources.length > 0) {
                  setMessageSources((prev) => ({ ...prev, [event.message_id]: event.sources! }));
                }
                traceEventsRef.current = [];
                setStreamingTraceEvents([]);
                setStreamingContent(null);
                setIsStreaming(false);

                // Notify parent to refetch conversations (auto-title update)
                if (messageCountRef.current === 1) {
                  onConversationUpdated?.();
                }
              } else if (event.type === "stopped") {
                // Capture trace snapshot
                const traceSnapshot = traceEventsRef.current;

                // Partial content saved on backend — persist locally
                const partialMsg: Message = {
                  id: event.message_id,
                  conversation_id: conversationId,
                  role: "assistant",
                  content: accumulated,
                  trace_data: null,
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, partialMsg]);
                if (traceSnapshot.length > 0) {
                  setMessageTraces((prev) => ({ ...prev, [event.message_id]: traceSnapshot }));
                }
                traceEventsRef.current = [];
                setStreamingTraceEvents([]);
                setStreamingContent(null);
                setIsStreaming(false);
              } else if (event.type === "error") {
                setError(event.message);
                traceEventsRef.current = [];
                setStreamingTraceEvents([]);
                setStreamingContent(null);
                setIsStreaming(false);
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          // User stopped generation — streaming content is preserved
          // until "stopped" SSE event arrives (or not)
          setStreamingContent(null);
          setIsStreaming(false);
        } else {
          setError((err as Error).message || "Stream failed");
          setStreamingContent(null);
          setIsStreaming(false);
        }
      } finally {
        abortControllerRef.current = null;
      }
    },
    [conversationId, token, isStreaming, onConversationUpdated],
  );

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  const regenerate = useCallback(async () => {
    if (!conversationId || !token || isStreaming) return;

    // Find the last user message content before regenerating
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUserMsg) return;

    try {
      await regenerateLastMessage(token, conversationId);
      // Remove last assistant message from local state
      setMessages((prev) => {
        const copy = [...prev];
        for (let i = copy.length - 1; i >= 0; i--) {
          if (copy[i].role === "assistant") {
            copy.splice(i, 1);
            break;
          }
        }
        return copy;
      });
      // Re-stream with the last user message
      await sendMessage(lastUserMsg.content);
    } catch {
      setError("Failed to regenerate message");
    }
  }, [conversationId, token, isStreaming, messages, sendMessage]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  return {
    messages,
    streamingContent,
    isStreaming,
    error,
    sendMessage,
    stopGeneration,
    regenerate,
    messageTraces,
    streamingTraceEvents,
    messageSources,
  };
}
