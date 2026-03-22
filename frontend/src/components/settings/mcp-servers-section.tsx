"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Loader2, Code2, FormInput } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/auth-context";
import {
  listMcpServers,
  createMcpServer,
  updateMcpServer,
  deleteMcpServer,
  toggleMcpServer,
} from "@/lib/mcp-api";
import type { McpServerCreate, McpServerUpdate } from "@/lib/mcp-api";
import { cn } from "@/lib/utils";
import { McpServerCard } from "./mcp-server-card";
import { McpServerForm } from "./mcp-server-form";
import { McpJsonEditor } from "./mcp-json-editor";

export function McpServersSection() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [viewMode, setViewMode] = useState<"form" | "json">("form");

  const {
    data: servers,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["mcp-servers"],
    queryFn: () => listMcpServers(token!),
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: (data: McpServerCreate) => createMcpServer(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
      setShowAddForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: McpServerUpdate }) =>
      updateMcpServer(token!, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteMcpServer(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => toggleMcpServer(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    },
  });

  async function handleCreate(data: McpServerCreate | McpServerUpdate) {
    await createMutation.mutateAsync(data as McpServerCreate);
  }

  async function handleUpdate(id: number, data: McpServerUpdate) {
    await updateMutation.mutateAsync({ id, data });
  }

  async function handleDelete(id: number) {
    await deleteMutation.mutateAsync(id);
  }

  async function handleToggle(id: number) {
    await toggleMutation.mutateAsync(id);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="text-muted-foreground size-6 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-destructive rounded-md bg-destructive/10 p-4 text-sm">
        Failed to load MCP servers: {error.message}
      </div>
    );
  }

  function handleImportSuccess() {
    queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    setViewMode("form");
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground text-sm">
          Configure MCP servers to enable external tool use in chat.
        </p>
        <div className="flex items-center gap-2">
          <div className="flex gap-1 rounded-md border p-1" role="radiogroup" aria-label="View mode">
            <button
              type="button"
              role="radio"
              aria-checked={viewMode === "form"}
              className={cn(
                "flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium transition-colors",
                viewMode === "form"
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted text-muted-foreground"
              )}
              onClick={() => setViewMode("form")}
            >
              <FormInput className="size-4" />
              Form
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={viewMode === "json"}
              className={cn(
                "flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium transition-colors",
                viewMode === "json"
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted text-muted-foreground"
              )}
              onClick={() => setViewMode("json")}
            >
              <Code2 className="size-4" />
              JSON
            </button>
          </div>
          {viewMode === "form" && !showAddForm && (
            <Button size="sm" onClick={() => setShowAddForm(true)}>
              <Plus data-icon="inline-start" />
              Add MCP Server
            </Button>
          )}
        </div>
      </div>

      {viewMode === "json" ? (
        <McpJsonEditor onImportSuccess={handleImportSuccess} servers={servers ?? []} />
      ) : (
        <>
          {showAddForm && (
            <McpServerForm
              onSubmit={handleCreate}
              onCancel={() => setShowAddForm(false)}
            />
          )}

          {servers && servers.length > 0 ? (
            <div className="space-y-3">
              {servers.map((server) => (
                <McpServerCard
                  key={server.id}
                  server={server}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
                  onToggle={handleToggle}
                />
              ))}
            </div>
          ) : (
            !showAddForm && (
              <div className="text-muted-foreground rounded-md border border-dashed p-8 text-center text-sm">
                No MCP servers yet. Add one to enable tool use.
              </div>
            )
          )}
        </>
      )}
    </div>
  );
}
