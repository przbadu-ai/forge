"use client";

import { useState } from "react";
import { Activity, Zap, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TraceEvent } from "@/types/chat";

interface TracePanelProps {
  events: TraceEvent[];
  isStreaming?: boolean;
}

function truncateJson(val: unknown, maxLen = 200): string {
  const str = JSON.stringify(val);
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "\u2026";
}

function formatDuration(startedAt: string, completedAt: string): string {
  const start = new Date(startedAt).getTime();
  const end = new Date(completedAt).getTime();
  const ms = end - start;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getEventIcon(type: TraceEvent["type"]) {
  switch (type) {
    case "run_start":
    case "run_end":
      return <Activity className="h-3.5 w-3.5" />;
    case "token_generation":
      return <Zap className="h-3.5 w-3.5" />;
    case "error":
      return <AlertCircle className="h-3.5 w-3.5" />;
  }
}

function getStatusClasses(status: TraceEvent["status"]): string {
  switch (status) {
    case "running":
      return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
    case "completed":
      return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
    case "error":
      return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
  }
}

export function TracePanel({ events, isStreaming }: TracePanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (events.length === 0 && !isStreaming) return null;

  return (
    <div className="mt-2 border-t border-muted pt-2">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {isOpen ? (
          <ChevronUp className="h-3.5 w-3.5" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5" />
        )}
        <span className="font-medium">Execution Trace</span>
        <span className="rounded-full bg-muted-foreground/20 px-1.5 py-0.5 text-[10px] leading-none">
          {events.length}
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 space-y-1.5">
          {events.map((event) => (
            <div
              key={event.id}
              className="flex flex-col gap-1 rounded-md bg-muted/50 px-2.5 py-1.5 text-xs"
            >
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">
                  {getEventIcon(event.type)}
                </span>
                <span className="font-medium truncate max-w-[200px]">
                  {event.name.length > 40
                    ? event.name.slice(0, 40) + "\u2026"
                    : event.name}
                </span>
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[10px] font-medium leading-none",
                    getStatusClasses(event.status),
                  )}
                >
                  {event.status}
                </span>
                <span className="ml-auto text-muted-foreground">
                  {event.completed_at && event.started_at
                    ? formatDuration(event.started_at, event.completed_at)
                    : formatTime(event.started_at)}
                </span>
              </div>

              {event.error && (
                <p className="text-red-600 dark:text-red-400 truncate">
                  {event.error.length > 100
                    ? event.error.slice(0, 100) + "\u2026"
                    : event.error}
                </p>
              )}

              {(event.input !== undefined || event.output !== undefined) && (
                <div className="flex flex-col gap-0.5 text-muted-foreground">
                  {event.input !== undefined && (
                    <code className="block truncate font-mono text-[11px]">
                      in: {truncateJson(event.input)}
                    </code>
                  )}
                  {event.output !== undefined && (
                    <code className="block truncate font-mono text-[11px]">
                      out: {truncateJson(event.output)}
                    </code>
                  )}
                </div>
              )}
            </div>
          ))}

          {isStreaming && (
            <div className="flex items-center gap-2 px-2.5 py-1 text-xs text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-yellow-500 animate-pulse" />
              Recording...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
