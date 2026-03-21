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
import { Pencil, Trash2, Wifi, Check, X, Loader2 } from "lucide-react";
import type { ProviderRead, TestConnectionResult } from "@/lib/providers-api";
import { ProviderForm } from "./provider-form";
import type { ProviderUpdate } from "@/lib/providers-api";

interface ProviderCardProps {
  provider: ProviderRead;
  onUpdate: (id: number, data: ProviderUpdate) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onTest: (baseUrl: string) => Promise<TestConnectionResult>;
}

export function ProviderCard({
  provider,
  onUpdate,
  onDelete,
  onTest,
}: ProviderCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionResult | null>(
    null
  );

  async function handleDelete() {
    if (!confirm(`Delete provider "${provider.name}"?`)) return;
    setIsDeleting(true);
    try {
      await onDelete(provider.id);
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleTest() {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await onTest(provider.base_url);
      setTestResult(result);
    } catch (err) {
      setTestResult({
        ok: false,
        error: err instanceof Error ? err.message : "Test failed",
      });
    } finally {
      setIsTesting(false);
    }
  }

  async function handleUpdate(data: ProviderUpdate) {
    await onUpdate(provider.id, data);
    setIsEditing(false);
  }

  if (isEditing) {
    return (
      <ProviderForm
        provider={provider}
        onSubmit={handleUpdate}
        onCancel={() => setIsEditing(false)}
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {provider.name}
          {provider.is_default && (
            <Badge variant="secondary">Default</Badge>
          )}
        </CardTitle>
        <CardAction>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setIsEditing(true)}
              title="Edit"
            >
              <Pencil />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={handleTest}
              disabled={isTesting}
              title="Test Connection"
            >
              {isTesting ? <Loader2 className="animate-spin" /> : <Wifi />}
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
        <p className="text-muted-foreground text-xs break-all">
          {provider.base_url}
        </p>
        {provider.models.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {provider.models.map((model) => (
              <Badge key={model} variant="outline">
                {model}
              </Badge>
            ))}
          </div>
        )}
        {provider.models.length === 0 && (
          <p className="text-muted-foreground text-xs">No models configured</p>
        )}

        {testResult && (
          <div
            className={`mt-2 flex items-center gap-2 rounded-md p-2 text-xs ${
              testResult.ok
                ? "bg-green-500/10 text-green-700 dark:text-green-400"
                : "bg-destructive/10 text-destructive"
            }`}
          >
            {testResult.ok ? (
              <>
                <Check className="size-3.5" />
                Connected in {testResult.latency_ms}ms
                {testResult.model_count != null &&
                  ` - ${testResult.model_count} model${testResult.model_count === 1 ? "" : "s"} available`}
              </>
            ) : (
              <>
                <X className="size-3.5" />
                {testResult.error}
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
