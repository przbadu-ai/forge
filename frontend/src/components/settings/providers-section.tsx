"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/auth-context";
import {
  listProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  testConnection,
} from "@/lib/providers-api";
import type {
  ProviderCreate,
  ProviderUpdate,
  TestConnectionResult,
} from "@/lib/providers-api";
import { ProviderCard } from "./provider-card";
import { ProviderForm } from "./provider-form";

export function ProvidersSection() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);

  const {
    data: providers,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["providers"],
    queryFn: () => listProviders(token!),
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: (data: ProviderCreate) => createProvider(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      setShowAddForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProviderUpdate }) =>
      updateProvider(token!, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteProvider(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });

  async function handleCreate(data: ProviderCreate | ProviderUpdate) {
    await createMutation.mutateAsync(data as ProviderCreate);
  }

  async function handleUpdate(id: number, data: ProviderUpdate) {
    await updateMutation.mutateAsync({ id, data });
  }

  async function handleDelete(id: number) {
    await deleteMutation.mutateAsync(id);
  }

  async function handleTest(baseUrl: string): Promise<TestConnectionResult> {
    // We don't have the api_key on the client (it's never returned).
    // Send empty string; the backend will use "ollama" as default.
    return testConnection(token!, baseUrl, "");
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
        Failed to load providers: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground text-sm">
          Configure LLM providers for chat. At least one provider is needed to
          start chatting.
        </p>
        {!showAddForm && (
          <Button size="sm" onClick={() => setShowAddForm(true)}>
            <Plus data-icon="inline-start" />
            Add Provider
          </Button>
        )}
      </div>

      {showAddForm && (
        <ProviderForm
          onSubmit={handleCreate}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      {providers && providers.length > 0 ? (
        <div className="space-y-3">
          {providers.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
              onTest={handleTest}
            />
          ))}
        </div>
      ) : (
        !showAddForm && (
          <div className="text-muted-foreground rounded-md border border-dashed p-8 text-center text-sm">
            No providers yet. Add one to start chatting.
          </div>
        )
      )}
    </div>
  );
}
