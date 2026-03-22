"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { ExecutionStep } from "./ExecutionStep";
import { SourceCitations, type SourceCitation } from "./source-citations";
import { User, Bot } from "lucide-react";
import type { TraceEvent } from "@/types/chat";
import { classifyTraceEvents } from "@/lib/trace-utils";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  traceEvents?: TraceEvent[];
  liveTraceEvents?: TraceEvent[];
  sources?: SourceCitation[];
}

export function MessageBubble({
  role,
  content,
  isStreaming,
  traceEvents,
  liveTraceEvents,
  sources,
}: MessageBubbleProps) {
  const isUser = role === "user";
  const activeTraceEvents = traceEvents ?? liveTraceEvents ?? [];
  const stepGroups = useMemo(
    () => classifyTraceEvents(activeTraceEvents),
    [activeTraceEvents]
  );

  // User message — keep the existing bubble style
  if (isUser) {
    return (
      <div className="flex justify-end gap-3 py-4">
        <div className="bg-primary text-primary-foreground max-w-[80%] rounded-2xl px-4 py-2.5">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>
        <div className="bg-primary/10 text-primary flex h-7 w-7 shrink-0 items-center justify-center rounded-full">
          <User className="h-4 w-4" />
        </div>
      </div>
    );
  }

  // Assistant message — independent sequential blocks, no shared background
  const showThinking = !!isStreaming && !content && stepGroups.length === 0;

  return (
    <div className="flex justify-start gap-3 py-4">
      {/* Bot avatar */}
      <div className="bg-primary/10 text-primary mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full">
        <Bot className="h-4 w-4" />
      </div>

      {/* Content column — no background wrapper */}
      <div
        className={cn(
          "max-w-[80%] min-w-0",
          stepGroups.length > 0 || content ? "space-y-3" : ""
        )}
      >
        {/* Thinking indicator — shown while streaming before any content or steps */}
        <ThinkingIndicator isVisible={showThinking} />

        {/* Execution steps as independent blocks */}
        {stepGroups.length > 0 && (
          <div className="space-y-1">
            {stepGroups.map((group, i) => (
              <ExecutionStep key={`step-${i}`} group={group} />
            ))}
          </div>
        )}

        {/* Markdown response — clean prose without background */}
        {content && (
          <div>
            <MarkdownRenderer content={content} />
            {isStreaming && (
              <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-current" />
            )}
          </div>
        )}

        {/* Source citations */}
        {sources && sources.length > 0 && <SourceCitations sources={sources} />}
      </div>
    </div>
  );
}
