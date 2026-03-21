"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardAction,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Pencil, Trash2, Loader2 } from "lucide-react";
import type { McpServerRead, McpServerUpdate } from "@/lib/mcp-api";
import { McpServerForm } from "./mcp-server-form";

interface McpServerCardProps {
  server: McpServerRead;
  onUpdate: (id: number, data: McpServerUpdate) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onToggle: (id: number) => Promise<void>;
}

export function McpServerCard({
  server,
  onUpdate,
  onDelete,
  onToggle,
}: McpServerCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isToggling, setIsToggling] = useState(false);

  async function handleDelete() {
    if (!confirm(`Delete MCP server "${server.name}"?`)) return;
    setIsDeleting(true);
    try {
      await onDelete(server.id);
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleToggle() {
    setIsToggling(true);
    try {
      await onToggle(server.id);
    } finally {
      setIsToggling(false);
    }
  }

  async function handleUpdate(data: McpServerUpdate) {
    await onUpdate(server.id, data);
    setIsEditing(false);
  }

  if (isEditing) {
    return (
      <McpServerForm
        server={server}
        onSubmit={handleUpdate}
        onCancel={() => setIsEditing(false)}
      />
    );
  }

  const argsPreview = server.args.length > 0 ? server.args.join(" ") : "";
  const commandPreview = argsPreview
    ? `${server.command} ${argsPreview}`
    : server.command;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {server.name}
          <Badge variant={server.is_enabled ? "secondary" : "outline"}>
            {server.is_enabled ? "Enabled" : "Disabled"}
          </Badge>
        </CardTitle>
        <CardAction>
          <div className="flex items-center gap-1">
            <Switch
              size="sm"
              checked={server.is_enabled}
              onCheckedChange={handleToggle}
              disabled={isToggling}
              aria-label={`Toggle ${server.name}`}
            />
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setIsEditing(true)}
              title="Edit"
            >
              <Pencil />
            </Button>
            <Button
              variant="destructive"
              size="icon-sm"
              onClick={handleDelete}
              disabled={isDeleting}
              title="Delete"
            >
              {isDeleting ? <Loader2 className="animate-spin" /> : <Trash2 />}
            </Button>
          </div>
        </CardAction>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-muted-foreground truncate font-mono text-xs">
          {commandPreview}
        </p>
        {Object.keys(server.env_vars).length > 0 && (
          <div className="flex flex-wrap gap-1">
            {Object.keys(server.env_vars).map((key) => (
              <Badge key={key} variant="outline">
                {key}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
