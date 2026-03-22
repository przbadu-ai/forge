import type { TraceEvent } from "@/types/chat";

export type StepCategory =
  | "thinking"
  | "tool_call"
  | "web_search"
  | "execution";

export interface ExecutionStepGroup {
  category: StepCategory;
  events: TraceEvent[];
  summary: string;
  isRunning: boolean;
  totalDurationMs: number;
}

// --- Shared formatters (moved from TracePanel) ---

export function truncateJson(val: unknown, maxLen = 200): string {
  const str = JSON.stringify(val);
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "\u2026";
}

export function formatDuration(startedAt: string, completedAt: string): string {
  const start = new Date(startedAt).getTime();
  const end = new Date(completedAt).getTime();
  const ms = end - start;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatDurationMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// --- Classification ---

function classifyEvent(event: TraceEvent): StepCategory {
  const name = event.name.toLowerCase();

  if (event.type === "token_generation" || name.includes("think")) {
    return "thinking";
  }

  if (
    name.includes("search") ||
    name.includes("web") ||
    name.includes("fetch") ||
    name.includes("browse")
  ) {
    return "web_search";
  }

  if (
    name.includes("tool") ||
    name.includes("read") ||
    name.includes("write") ||
    name.includes("list") ||
    name.includes("function") ||
    name.includes("execute") ||
    name.includes("command") ||
    name.includes("call") ||
    name.includes("query") ||
    name.includes("api")
  ) {
    return "tool_call";
  }

  return "execution";
}

// --- Summary generation ---

function generateSummary(category: StepCategory, events: TraceEvent[]): string {
  if (events.length === 1) {
    const name = events[0].name;
    return name.length > 50 ? name.slice(0, 50) + "\u2026" : name;
  }

  switch (category) {
    case "thinking":
      return "Thinking\u2026";

    case "web_search": {
      const count = events.length;
      return count === 1 ? "Searched the web" : `${count} web searches`;
    }

    case "tool_call": {
      // Group by verb extracted from event names for richer summary
      const verbs: Record<string, number> = {};
      for (const e of events) {
        const name = e.name.toLowerCase();
        if (name.includes("read")) verbs["Read"] = (verbs["Read"] || 0) + 1;
        else if (name.includes("write"))
          verbs["Wrote"] = (verbs["Wrote"] || 0) + 1;
        else if (
          name.includes("command") ||
          name.includes("execute") ||
          name.includes("run")
        )
          verbs["Ran"] = (verbs["Ran"] || 0) + 1;
        else if (name.includes("search") || name.includes("query"))
          verbs["Searched"] = (verbs["Searched"] || 0) + 1;
        else verbs["Called"] = (verbs["Called"] || 0) + 1;
      }

      const parts = Object.entries(verbs).map(([verb, count]) => {
        if (verb === "Read")
          return `Read ${count} file${count !== 1 ? "s" : ""}`;
        if (verb === "Wrote")
          return `Wrote ${count} file${count !== 1 ? "s" : ""}`;
        if (verb === "Ran")
          return `Ran ${count} command${count !== 1 ? "s" : ""}`;
        if (verb === "Searched")
          return `${count} search${count !== 1 ? "es" : ""}`;
        return `${count} tool call${count !== 1 ? "s" : ""}`;
      });

      return parts.join(", ");
    }

    case "execution":
      return `${events.length} step${events.length !== 1 ? "s" : ""}`;
  }
}

// --- Grouping ---

function computeDuration(events: TraceEvent[]): number {
  let total = 0;
  for (const e of events) {
    if (e.started_at && e.completed_at) {
      total +=
        new Date(e.completed_at).getTime() - new Date(e.started_at).getTime();
    }
  }
  return total;
}

export function classifyTraceEvents(
  events: TraceEvent[]
): ExecutionStepGroup[] {
  if (events.length === 0) return [];

  const groups: ExecutionStepGroup[] = [];
  let currentCategory = classifyEvent(events[0]);
  let currentEvents: TraceEvent[] = [events[0]];

  for (let i = 1; i < events.length; i++) {
    const cat = classifyEvent(events[i]);
    if (cat === currentCategory) {
      currentEvents.push(events[i]);
    } else {
      groups.push({
        category: currentCategory,
        events: currentEvents,
        summary: generateSummary(currentCategory, currentEvents),
        isRunning: currentEvents.some((e) => e.status === "running"),
        totalDurationMs: computeDuration(currentEvents),
      });
      currentCategory = cat;
      currentEvents = [events[i]];
    }
  }

  // Push last group
  groups.push({
    category: currentCategory,
    events: currentEvents,
    summary: generateSummary(currentCategory, currentEvents),
    isRunning: currentEvents.some((e) => e.status === "running"),
    totalDurationMs: computeDuration(currentEvents),
  });

  return groups;
}
