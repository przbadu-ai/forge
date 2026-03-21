"use client";

import { useCallback, useEffect, useRef } from "react";
import { useAuth } from "@/context/auth-context";
import { useChat } from "@/hooks/useChat";
import { exportConversation } from "@/lib/chat-api";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { Button } from "@/components/ui/button";
import { Download, RefreshCw } from "lucide-react";

interface ChatPanelProps {
  conversationId: number;
  onConversationUpdated?: () => void;
}

export function ChatPanel({
  conversationId,
  onConversationUpdated,
}: ChatPanelProps) {
  const { token } = useAuth();
  const {
    messages,
    streamingContent,
    isStreaming,
    error,
    sendMessage,
    stopGeneration,
    regenerate,
  } = useChat({ conversationId, onConversationUpdated });

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

  const handleExport = useCallback(async () => {
    if (!token) return;
    try {
      const blob = await exportConversation(token, conversationId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `conversation-${conversationId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // Export failed silently
    }
  }, [token, conversationId]);

  const handleRegenerate = useCallback(() => {
    void regenerate();
  }, [regenerate]);

  const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
  const showRegenerate =
    !isStreaming && lastMessage && lastMessage.role === "assistant";

  return (
    <div className="flex h-full flex-col">
      {/* Header with export */}
      <div className="flex items-center justify-end border-b px-4 py-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => void handleExport()}
          aria-label="Export conversation"
        >
          <Download className="h-4 w-4" />
        </Button>
      </div>

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

          {showRegenerate && (
            <div className="flex justify-start pl-10 pb-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRegenerate}
                aria-label="Regenerate response"
              >
                <RefreshCw className="mr-1 h-3.5 w-3.5" />
                Regenerate
              </Button>
            </div>
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
        <ChatInput
          onSend={handleSend}
          onStop={stopGeneration}
          isStreaming={isStreaming}
          disabled={isStreaming}
        />
      </div>
    </div>
  );
}
