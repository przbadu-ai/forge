"use client";

import { useEffect, useState } from "react";
import { useGeneralSettings } from "@/hooks/useGeneralSettings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";

export function GeneralSection() {
  const { settings, isLoading, updateSettings } = useGeneralSettings();
  const [systemPrompt, setSystemPrompt] = useState("");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) {
      setSystemPrompt(settings.system_prompt ?? "");
      setTemperature(settings.temperature);
      setMaxTokens(settings.max_tokens);
    }
  }, [settings]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await updateSettings({
        system_prompt: systemPrompt || null,
        temperature,
        max_tokens: maxTokens,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // Error handled by mutation
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="text-muted-foreground size-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <p className="text-muted-foreground text-sm">
        Configure default model parameters for all conversations.
      </p>

      <div className="space-y-2">
        <Label htmlFor="system-prompt">
          Custom Instructions / System Prompt
        </Label>
        <textarea
          id="system-prompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="You are a helpful assistant..."
          rows={4}
          className="flex w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50"
          aria-label="System prompt"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="temperature">
          Temperature: {temperature.toFixed(1)}
        </Label>
        <input
          id="temperature"
          type="range"
          min={0}
          max={2}
          step={0.1}
          value={temperature}
          onChange={(e) => setTemperature(parseFloat(e.target.value))}
          className="w-full"
          aria-label="Temperature"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>0.0 (Precise)</span>
          <span>2.0 (Creative)</span>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="max-tokens">Max Tokens</Label>
        <Input
          id="max-tokens"
          type="number"
          min={1}
          max={32768}
          value={maxTokens}
          onChange={(e) => setMaxTokens(parseInt(e.target.value) || 1)}
          aria-label="Max tokens"
        />
      </div>

      <Button onClick={() => void handleSave()} disabled={saving}>
        {saving ? (
          <>
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            Saving...
          </>
        ) : saved ? (
          "Saved!"
        ) : (
          "Save"
        )}
      </Button>
    </div>
  );
}
