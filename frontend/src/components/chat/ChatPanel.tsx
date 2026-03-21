"use client";

import { useCallback, useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

interface ChatPanelProps {
  conversationId: number;
  onConversationUpdated?: () => void;
}

export function ChatPanel({
  conversationId,
  onConversationUpdated,
}: ChatPanelProps) {
  const { messages, streamingContent, isStreaming, error, sendMessage } =
    useChat({ conversationId, onConversationUpdated });

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  // Detect user scroll
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const threshold = 50;
    userScrolledUp.current =
      el.scrollTop + el.clientHeight < el.scrollHeight - threshold;
  }, []);

  // Auto-scroll when new content arrives
  useEffect(() => {
    if (!userScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, streamingContent]);

  const handleSend = useCallback(
    (content: string) => {
      void sendMessage(content);
    },
    [sendMessage],
  );

  return (
    <div className="flex h-full flex-col">
      {/* Messages area */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 md:px-8"
      >
        <div className="mx-auto max-w-3xl">
          {messages.length === 0 && !isStreaming && (
            <div className="flex h-full items-center justify-center py-20">
              <p className="text-muted-foreground">
                Send a message to start the conversation.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              role={msg.role as "user" | "assistant"}
              content={msg.content}
            />
          ))}

          {streamingContent !== null && (
            <MessageBubble
              role="assistant"
              content={streamingContent}
              isStreaming
            />
          )}

          {error && (
            <div className="my-4 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={handleSend} disabled={isStreaming} />
      </div>
    </div>
  );
}
