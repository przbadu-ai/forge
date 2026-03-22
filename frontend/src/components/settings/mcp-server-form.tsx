"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  McpServerRead,
  McpServerCreate,
  McpServerUpdate,
  McpTransportType,
} from "@/lib/mcp-api";

interface McpServerFormProps {
  server?: McpServerRead;
  onSubmit: (data: McpServerCreate | McpServerUpdate) => Promise<void>;
  onCancel: () => void;
}

const TRANSPORT_OPTIONS: { value: McpTransportType; label: string }[] = [
  { value: "stdio", label: "Local (stdio)" },
  { value: "sse", label: "SSE" },
  { value: "streamable_http", label: "Streamable HTTP" },
];

export function McpServerForm({ server, onSubmit, onCancel }: McpServerFormProps) {
  const isEditing = !!server;

  const [name, setName] = useState(server?.name ?? "");
  const [transportType, setTransportType] = useState<McpTransportType>(
    server?.transport_type ?? "stdio"
  );
  const [command, setCommand] = useState(server?.command ?? "");
  const [args, setArgs] = useState(server?.args?.join("\n") ?? "");
  const [url, setUrl] = useState(server?.url ?? "");
  const [envVars, setEnvVars] = useState(
    server?.env_vars
      ? Object.entries(server.env_vars)
          .map(([k, v]) => `${k}=${v}`)
          .join("\n")
      : ""
  );
  const [isEnabled, setIsEnabled] = useState(server?.is_enabled ?? true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isStdio = transportType === "stdio";
  const isRemote = transportType === "sse" || transportType === "streamable_http";

  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    if (!name.trim()) newErrors.name = "Name is required";
    if (isStdio && !command.trim()) newErrors.command = "Command is required";
    if (isRemote && !url.trim()) newErrors.url = "URL is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function parseArgs(raw: string): string[] {
    return raw
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }

  function parseEnvVars(raw: string): Record<string, string> {
    const result: Record<string, string> = {};
    for (const line of raw.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const eqIndex = trimmed.indexOf("=");
      if (eqIndex > 0) {
        result[trimmed.slice(0, eqIndex)] = trimmed.slice(eqIndex + 1);
      }
    }
    return result;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const data: McpServerCreate | McpServerUpdate = {
        name: name.trim(),
        transport_type: transportType,
        command: isStdio ? command.trim() : null,
        args: isStdio ? parseArgs(args) : [],
        url: isRemote ? url.trim() : null,
        env_vars: parseEnvVars(envVars),
        is_enabled: isEnabled,
      };
      await onSubmit(data);
    } catch {
      // Error handling is done by the caller
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEditing ? "Edit MCP Server" : "Add MCP Server"}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="mcp-name">Name</Label>
            <Input
              id="mcp-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. filesystem, github"
              aria-invalid={!!errors.name}
            />
            {errors.name && (
              <p className="text-destructive text-xs">{errors.name}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>Transport Type</Label>
            <div className="flex gap-1 rounded-md border p-1" role="radiogroup" aria-label="Transport type">
              {TRANSPORT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  role="radio"
                  aria-checked={transportType === opt.value}
                  className={cn(
                    "flex-1 rounded px-3 py-1.5 text-sm font-medium transition-colors",
                    transportType === opt.value
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted text-muted-foreground"
                  )}
                  onClick={() => setTransportType(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {isStdio && (
            <>
              <div className="space-y-1.5">
                <Label htmlFor="mcp-command">Command</Label>
                <Input
                  id="mcp-command"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  placeholder="e.g. uvx, node, /usr/local/bin/mcp-server"
                  aria-invalid={!!errors.command}
                />
                {errors.command && (
                  <p className="text-destructive text-xs">{errors.command}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="mcp-args">Arguments</Label>
                <textarea
                  id="mcp-args"
                  className="border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-[3px] focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                  value={args}
                  onChange={(e) => setArgs(e.target.value)}
                  placeholder={"One argument per line\ne.g.\nmcp-server-filesystem\n/path/to/dir"}
                />
                <p className="text-muted-foreground text-xs">
                  One argument per line
                </p>
              </div>
            </>
          )}

          {isRemote && (
            <div className="space-y-1.5">
              <Label htmlFor="mcp-url">Server URL</Label>
              <Input
                id="mcp-url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={
                  transportType === "sse"
                    ? "http://localhost:8080/sse"
                    : "http://localhost:8080/mcp"
                }
                aria-invalid={!!errors.url}
              />
              {errors.url && (
                <p className="text-destructive text-xs">{errors.url}</p>
              )}
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="mcp-env-vars">Environment Variables</Label>
            <textarea
              id="mcp-env-vars"
              className="border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-[3px] focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
              value={envVars}
              onChange={(e) => setEnvVars(e.target.value)}
              placeholder={"KEY=VALUE, one per line\ne.g.\nGITHUB_TOKEN=ghp_xxx"}
            />
            <p className="text-muted-foreground text-xs">
              KEY=VALUE, one per line
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Switch
              id="mcp-enabled"
              checked={isEnabled}
              onCheckedChange={setIsEnabled}
            />
            <Label htmlFor="mcp-enabled">Enable server</Label>
          </div>

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="animate-spin" data-icon="inline-start" />}
              {isEditing ? "Update" : "Create"}
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
