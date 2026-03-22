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
  const [skillDirectories, setSkillDirectories] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) {
      setSystemPrompt(settings.system_prompt ?? "");
      setTemperature(settings.temperature);
      setMaxTokens(settings.max_tokens);
      setSkillDirectories((settings.skill_directories ?? []).join("\n"));
    }
  }, [settings]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const dirs = skillDirectories
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);
      await updateSettings({
        system_prompt: systemPrompt || null,
        temperature,
        max_tokens: maxTokens,
        skill_directories: dirs,
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
          className="border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-3 disabled:opacity-50"
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
        <div className="text-muted-foreground flex justify-between text-xs">
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

      <div className="space-y-2">
        <Label htmlFor="skill-directories">Skill Directories</Label>
        <textarea
          id="skill-directories"
          value={skillDirectories}
          onChange={(e) => setSkillDirectories(e.target.value)}
          placeholder={
            "One directory path per line\n/path/to/skills\n~/.claude/skills"
          }
          rows={3}
          className="border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-3 disabled:opacity-50"
          aria-label="Skill directories"
        />
        <p className="text-muted-foreground text-xs">
          Directories containing skill subdirectories with SKILL.md files. One
          path per line.
        </p>
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
