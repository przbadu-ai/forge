"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { getMessages } from "@/lib/chat-api";
import type { Message, SSEEvent } from "@/types/chat";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  const abortControllerRef = useRef<AbortController | null>(null);
  const messageCountRef = useRef(0);

  // Load messages when conversationId changes
  useEffect(() => {
    if (!conversationId || !token) {
      setMessages([]);
      return;
    }

    let cancelled = false;
    getMessages(token, conversationId)
      .then((msgs) => {
        if (!cancelled) {
          setMessages(msgs);
          messageCountRef.current = msgs.filter(
            (m) => m.role === "user",
          ).length;
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
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticUserMsg]);
      messageCountRef.current += 1;

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
              } else if (event.type === "done") {
                // Convert accumulated content into a Message
                const assistantMsg: Message = {
                  id: event.message_id,
                  conversation_id: conversationId,
                  role: "assistant",
                  content: accumulated,
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, assistantMsg]);
                setStreamingContent(null);
                setIsStreaming(false);

                // Notify parent to refetch conversations (auto-title update)
                if (messageCountRef.current === 1) {
                  onConversationUpdated?.();
                }
              } else if (event.type === "error") {
                setError(event.message);
                setStreamingContent(null);
                setIsStreaming(false);
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
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
  };
}
