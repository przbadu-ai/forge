"use client";

import { useState } from "react";
import {
  Brain,
  Terminal,
  Globe,
  Activity,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { TraceEvent } from "@/types/chat";
import {
  type ExecutionStepGroup,
  type StepCategory,
  truncateJson,
  formatDuration,
  formatDurationMs,
} from "@/lib/trace-utils";

interface ExecutionStepProps {
  group: ExecutionStepGroup;
}

const categoryConfig: Record<
  StepCategory,
  {
    icon: typeof Brain;
    borderClass: string;
    iconClass: string;
    dotClass: string;
  }
> = {
  thinking: {
    icon: Brain,
    borderClass: "border-l-purple-400 dark:border-l-purple-500",
    iconClass: "text-purple-500 dark:text-purple-400",
    dotClass: "bg-purple-500",
  },
  tool_call: {
    icon: Terminal,
    borderClass: "border-l-blue-400 dark:border-l-blue-500",
    iconClass: "text-blue-500 dark:text-blue-400",
    dotClass: "bg-blue-500",
  },
  web_search: {
    icon: Globe,
    borderClass: "border-l-emerald-400 dark:border-l-emerald-500",
    iconClass: "text-emerald-500 dark:text-emerald-400",
    dotClass: "bg-emerald-500",
  },
  execution: {
    icon: Activity,
    borderClass: "border-l-zinc-300 dark:border-l-zinc-600",
    iconClass: "text-zinc-500 dark:text-zinc-400",
    dotClass: "bg-zinc-500",
  },
};

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

export function ExecutionStep({ group }: ExecutionStepProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = categoryConfig[group.category];
  const Icon = config.icon;
  const isCollapsible = group.events.length > 1;

  return (
    <div className={cn("border-l-2 py-1 pl-3", config.borderClass)}>
      {/* Header / summary row */}
      <button
        type="button"
        onClick={() => isCollapsible && setIsExpanded((prev) => !prev)}
        className={cn(
          "text-muted-foreground flex w-full items-center gap-2 text-xs transition-colors",
          isCollapsible && "hover:text-foreground cursor-pointer",
          !isCollapsible && "cursor-default"
        )}
      >
        {/* Running indicator or icon */}
        {group.isRunning ? (
          <span
            className={cn(
              "h-2 w-2 shrink-0 animate-pulse rounded-full",
              config.dotClass
            )}
          />
        ) : (
          <Icon className={cn("h-3.5 w-3.5 shrink-0", config.iconClass)} />
        )}

        <span className="text-foreground/80 truncate font-medium">
          {group.summary}
        </span>

        {group.totalDurationMs > 0 && (
          <span className="ml-auto shrink-0 tabular-nums">
            {formatDurationMs(group.totalDurationMs)}
          </span>
        )}

        {isCollapsible && (
          <span className="shrink-0">
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </span>
        )}
      </button>

      {/* Expanded event details */}
      {isExpanded && (
        <div className="mt-1.5 space-y-1 pl-5">
          {group.events.map((event) => (
            <div key={event.id} className="flex flex-col gap-0.5 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-foreground/70 max-w-[240px] truncate font-mono text-[11px]">
                  {event.name}
                </span>
                <span
                  className={cn(
                    "shrink-0 rounded-full px-1.5 py-0.5 text-[10px] leading-none font-medium",
                    getStatusClasses(event.status)
                  )}
                >
                  {event.status}
                </span>
                <span className="text-muted-foreground ml-auto shrink-0 tabular-nums">
                  {event.completed_at && event.started_at
                    ? formatDuration(event.started_at, event.completed_at)
                    : ""}
                </span>
              </div>

              {event.error && (
                <p className="truncate text-[11px] text-red-600 dark:text-red-400">
                  {event.error.length > 120
                    ? event.error.slice(0, 120) + "\u2026"
                    : event.error}
                </p>
              )}

              {event.input !== undefined && event.input !== null && (
                <code className="text-muted-foreground block truncate font-mono text-[11px]">
                  in: {truncateJson(event.input, 150)}
                </code>
              )}
              {event.output !== undefined && event.output !== null && (
                <code className="text-muted-foreground block truncate font-mono text-[11px]">
                  out: {truncateJson(event.output, 150)}
                </code>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
