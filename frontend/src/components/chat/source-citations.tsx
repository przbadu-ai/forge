"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, FileText } from "lucide-react";

export interface SourceCitation {
  file_name: string;
  chunk_text: string;
  score: number;
}

interface SourceCitationsProps {
  sources: SourceCitation[];
}

export function SourceCitations({ sources }: SourceCitationsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (sources.length === 0) return null;

  return (
    <div className="mt-2 border-t pt-2">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-muted-foreground hover:text-foreground flex items-center gap-1 text-xs transition-colors"
        aria-expanded={isExpanded}
        aria-label="Toggle source citations"
      >
        {isExpanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        <FileText className="h-3 w-3" />
        <span>
          {sources.length} source{sources.length !== 1 ? "s" : ""}
        </span>
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, index) => (
            <div
              key={`source-${index}`}
              className="rounded border bg-background/50 p-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{source.file_name}</span>
                <span className="text-muted-foreground">
                  {(source.score * 100).toFixed(0)}% match
                </span>
              </div>
              <p className="text-muted-foreground mt-1 line-clamp-3">
                {source.chunk_text}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
