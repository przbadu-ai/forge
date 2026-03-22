"use client";

import { Sparkles } from "lucide-react";

interface ThinkingIndicatorProps {
  isVisible: boolean;
}

export function ThinkingIndicator({ isVisible }: ThinkingIndicatorProps) {
  if (!isVisible) return null;

  return (
    <div className="text-muted-foreground flex items-center gap-2 py-1.5 text-sm">
      <Sparkles className="h-4 w-4 text-purple-500 dark:text-purple-400" />
      <span className="font-medium">Thinking</span>
      <span className="flex items-center gap-0.5">
        <span className="h-1 w-1 animate-bounce rounded-full bg-purple-400 [animation-delay:0ms] dark:bg-purple-500" />
        <span className="h-1 w-1 animate-bounce rounded-full bg-purple-400 [animation-delay:150ms] dark:bg-purple-500" />
        <span className="h-1 w-1 animate-bounce rounded-full bg-purple-400 [animation-delay:300ms] dark:bg-purple-500" />
      </span>
    </div>
  );
}
