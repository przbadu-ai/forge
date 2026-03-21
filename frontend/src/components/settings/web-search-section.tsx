"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import {
  getWebSearchSettings,
  updateWebSearchSettings,
} from "@/lib/web-search-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";

export function WebSearchSection() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [searxngBaseUrl, setSearxngBaseUrl] = useState("");
  const [exaApiKey, setExaApiKey] = useState("");
  const [exaKeySet, setExaKeySet] = useState(false);

  useEffect(() => {
    if (!token) return;
    void (async () => {
      try {
        const data = await getWebSearchSettings(token);
        setSearxngBaseUrl(data.searxng_base_url ?? "");
        setExaKeySet(data.exa_api_key_set);
      } catch {
        // Failed to load settings
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  const handleSave = async () => {
    if (!token) return;
    setSaving(true);
    setSaved(false);
    try {
      const payload: Record<string, string | null> = {
        searxng_base_url: searxngBaseUrl || null,
      };
      // Only send exa_api_key if user typed a new one
      if (exaApiKey) {
        payload.exa_api_key = exaApiKey;
      }
      const updated = await updateWebSearchSettings(token, payload);
      setExaKeySet(updated.exa_api_key_set);
      setExaApiKey(""); // Clear after save
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // Error handled
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <p className="text-muted-foreground text-sm">
        Configure web search providers for internet-augmented responses.
      </p>

      <div className="space-y-4">
        <h3 className="text-sm font-medium">SearXNG (Self-hosted)</h3>
        <div className="space-y-2">
          <Label htmlFor="searxng-base-url">Base URL</Label>
          <Input
            id="searxng-base-url"
            value={searxngBaseUrl}
            onChange={(e) => setSearxngBaseUrl(e.target.value)}
            placeholder="http://localhost:8888"
            aria-label="SearXNG base URL"
          />
          <p className="text-muted-foreground text-xs">
            URL of your SearXNG instance. Leave empty to disable.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-medium">Exa Search (API)</h3>
        <div className="space-y-2">
          <Label htmlFor="exa-api-key">API Key</Label>
          <Input
            id="exa-api-key"
            type="password"
            value={exaApiKey}
            onChange={(e) => setExaApiKey(e.target.value)}
            placeholder={exaKeySet ? "********** (key saved)" : "Enter Exa API key"}
            aria-label="Exa API key"
          />
          <p className="text-muted-foreground text-xs">
            {exaKeySet
              ? "API key is configured. Enter a new key to replace it."
              : "Get your API key from exa.ai. Leave empty to disable."}
          </p>
        </div>
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
