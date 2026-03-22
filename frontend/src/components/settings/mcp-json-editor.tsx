"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { importMcpServers } from "@/lib/mcp-api";
import type { McpBulkImportResponse } from "@/lib/mcp-api";

const EXAMPLE_JSON = `{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxx"
      }
    }
  }
}`;

interface McpJsonEditorProps {
  onImportSuccess: () => void;
}

export function McpJsonEditor({ onImportSuccess }: McpJsonEditorProps) {
  const { token } = useAuth();
  const [jsonText, setJsonText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<McpBulkImportResponse | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  async function handleImport() {
    setError(null);
    setResult(null);

    let parsed: unknown;
    try {
      parsed = JSON.parse(jsonText);
    } catch {
      setError("Invalid JSON. Please check your syntax and try again.");
      return;
    }

    if (
      typeof parsed !== "object" ||
      parsed === null ||
      !("mcpServers" in parsed) ||
      typeof (parsed as Record<string, unknown>).mcpServers !== "object" ||
      (parsed as Record<string, unknown>).mcpServers === null
    ) {
      setError(
        'JSON must contain an "mcpServers" object. See the placeholder for the expected format.'
      );
      return;
    }

    setIsImporting(true);
    try {
      const response = await importMcpServers(
        token!,
        parsed as {
          mcpServers: Record<
            string,
            {
              command?: string;
              args?: string[];
              env?: Record<string, string>;
              url?: string;
            }
          >;
        }
      );
      setResult(response);
      setTimeout(() => {
        setJsonText("");
        setResult(null);
        onImportSuccess();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import from JSON</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-muted-foreground text-sm">
          Paste your Cursor or Claude Desktop mcp.json configuration below.
          Existing servers with matching names will be updated.
        </p>

        <textarea
          className="border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex min-h-[300px] w-full rounded-md border px-3 py-2 font-mono text-sm focus-visible:ring-[3px] focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          placeholder={EXAMPLE_JSON}
          disabled={isImporting}
        />

        {error && (
          <div className="text-destructive rounded-md bg-destructive/10 p-3 text-sm">
            {error}
          </div>
        )}

        {result && (
          <div className="rounded-md bg-green-500/10 p-3 text-sm text-green-700 dark:text-green-400">
            Created {result.created}, Updated {result.updated} server
            {result.created + result.updated !== 1 ? "s" : ""}
          </div>
        )}

        <Button
          onClick={handleImport}
          disabled={isImporting || !jsonText.trim()}
        >
          {isImporting && (
            <Loader2 className="animate-spin" data-icon="inline-start" />
          )}
          Import Servers
        </Button>
      </CardContent>
    </Card>
  );
}
