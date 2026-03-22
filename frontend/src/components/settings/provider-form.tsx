"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import type {
  ProviderRead,
  ProviderCreate,
  ProviderUpdate,
} from "@/lib/providers-api";

interface ProviderFormProps {
  provider?: ProviderRead;
  onSubmit: (data: ProviderCreate | ProviderUpdate) => Promise<void>;
  onCancel: () => void;
}

export function ProviderForm({
  provider,
  onSubmit,
  onCancel,
}: ProviderFormProps) {
  const isEditing = !!provider;

  const [name, setName] = useState(provider?.name ?? "");
  const [baseUrl, setBaseUrl] = useState(provider?.base_url ?? "");
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState(provider?.models.join(", ") ?? "");
  const [isDefault, setIsDefault] = useState(provider?.is_default ?? false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    if (!name.trim()) newErrors.name = "Name is required";
    if (!baseUrl.trim()) newErrors.base_url = "Base URL is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const modelList = models
        .split(",")
        .map((m) => m.trim())
        .filter(Boolean);

      if (isEditing) {
        const data: ProviderUpdate = {
          name: name.trim(),
          base_url: baseUrl.trim(),
          models: modelList,
          is_default: isDefault,
        };
        // Only send api_key if user typed something
        if (apiKey) data.api_key = apiKey;
        await onSubmit(data);
      } else {
        const data: ProviderCreate = {
          name: name.trim(),
          base_url: baseUrl.trim(),
          api_key: apiKey,
          models: modelList,
          is_default: isDefault,
        };
        await onSubmit(data);
      }
    } catch {
      // Error handling is done by the caller
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEditing ? "Edit Provider" : "Add Provider"}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="provider-name">Name</Label>
            <Input
              id="provider-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Ollama, OpenAI"
              aria-invalid={!!errors.name}
            />
            {errors.name && (
              <p className="text-destructive text-xs">{errors.name}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="provider-base-url">Base URL</Label>
            <Input
              id="provider-base-url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="e.g. http://localhost:11434/v1"
              aria-invalid={!!errors.base_url}
            />
            {errors.base_url && (
              <p className="text-destructive text-xs">{errors.base_url}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="provider-api-key">API Key</Label>
            <Input
              id="provider-api-key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={
                isEditing ? "Leave blank to keep existing" : "Optional"
              }
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="provider-models">Models</Label>
            <Input
              id="provider-models"
              value={models}
              onChange={(e) => setModels(e.target.value)}
              placeholder="e.g. gpt-4, gpt-3.5-turbo (comma-separated)"
            />
            <p className="text-muted-foreground text-xs">
              Comma-separated list of model names
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Switch
              id="provider-default"
              checked={isDefault}
              onCheckedChange={setIsDefault}
            />
            <Label htmlFor="provider-default">Set as default provider</Label>
          </div>

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="animate-spin" data-icon="inline-start" />
              )}
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
