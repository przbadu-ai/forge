"use client";

import { useCallback } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import { cn } from "@/lib/utils";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({
  content,
  className,
}: MarkdownRendererProps) {
  const CopyButton = useCallback(({ text }: { text: string }) => {
    const handleCopy = () => {
      void navigator.clipboard.writeText(text);
    };
    return (
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 rounded bg-white/10 px-2 py-1 text-xs text-gray-300 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-white/20"
        aria-label="Copy code"
      >
        Copy
      </button>
    );
  }, []);

  const components: Components = {
    pre({ children, ...props }) {
      // Extract the text content from the code element for copy button
      const codeElement = children as React.ReactElement<{
        children?: string;
      }>;
      const codeText =
        typeof codeElement === "object" &&
        codeElement !== null &&
        "props" in codeElement
          ? String(codeElement.props.children ?? "")
          : "";

      return (
        <div className="group relative">
          <pre
            className="overflow-x-auto rounded-lg bg-zinc-900 p-4 text-sm dark:bg-zinc-950"
            {...props}
          >
            {children}
          </pre>
          <CopyButton text={codeText} />
        </div>
      );
    },
    code({ className: codeClassName, children, ...props }) {
      // Inline code (no language class from highlight)
      const isInline = !codeClassName;
      if (isInline) {
        return (
          <code
            className="rounded bg-zinc-200 px-1.5 py-0.5 font-mono text-sm dark:bg-zinc-800"
            {...props}
          >
            {children}
          </code>
        );
      }
      return (
        <code className={cn("font-mono", codeClassName)} {...props}>
          {children}
        </code>
      );
    },
    table({ children, ...props }) {
      return (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse" {...props}>
            {children}
          </table>
        </div>
      );
    },
    th({ children, ...props }) {
      return (
        <th
          className="border border-zinc-300 bg-zinc-100 px-3 py-2 text-left font-semibold dark:border-zinc-700 dark:bg-zinc-800"
          {...props}
        >
          {children}
        </th>
      );
    },
    td({ children, ...props }) {
      return (
        <td
          className="border border-zinc-300 px-3 py-2 dark:border-zinc-700"
          {...props}
        >
          {children}
        </td>
      );
    },
  };

  return (
    <div
      className={cn(
        "prose prose-sm dark:prose-invert max-w-none [&_li]:my-0.5 [&_ol]:my-2 [&_p]:leading-relaxed [&_ul]:my-2",
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize, [rehypeHighlight, { detect: true }]]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
