"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import {
  getEmbeddingSettings,
  updateEmbeddingSettings,
} from "@/lib/embeddings-api";
import type { EmbeddingSettings } from "@/lib/embeddings-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";

export function EmbeddingsSection() {
  const { token } = useAuth();
  const [_settings, setSettings] = useState<EmbeddingSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [embeddingBaseUrl, setEmbeddingBaseUrl] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("");
  const [rerankerBaseUrl, setRerankerBaseUrl] = useState("");
  const [rerankerModel, setRerankerModel] = useState("");

  useEffect(() => {
    if (!token) return;
    void (async () => {
      try {
        const data = await getEmbeddingSettings(token);
        setSettings(data);
        setEmbeddingBaseUrl(data.embedding_base_url ?? "");
        setEmbeddingModel(data.embedding_model ?? "");
        setRerankerBaseUrl(data.reranker_base_url ?? "");
        setRerankerModel(data.reranker_model ?? "");
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
      const updated = await updateEmbeddingSettings(token, {
        embedding_base_url: embeddingBaseUrl || null,
        embedding_model: embeddingModel || null,
        reranker_base_url: rerankerBaseUrl || null,
        reranker_model: rerankerModel || null,
      });
      setSettings(updated);
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
        Configure the embedding model endpoint for document retrieval (RAG) and
        an optional reranker for improved result quality.
      </p>

      <div className="space-y-4">
        <h3 className="text-sm font-medium">Embedding Model</h3>
        <div className="space-y-2">
          <Label htmlFor="embedding-base-url">Base URL</Label>
          <Input
            id="embedding-base-url"
            value={embeddingBaseUrl}
            onChange={(e) => setEmbeddingBaseUrl(e.target.value)}
            placeholder="http://localhost:11434"
            aria-label="Embedding base URL"
          />
          <p className="text-muted-foreground text-xs">
            OpenAI-compatible endpoint. Leave empty to use hash-based
            embeddings (dev/testing only).
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="embedding-model">Model Name</Label>
          <Input
            id="embedding-model"
            value={embeddingModel}
            onChange={(e) => setEmbeddingModel(e.target.value)}
            placeholder="nomic-embed-text"
            aria-label="Embedding model name"
          />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-medium">Reranker (Optional)</h3>
        <div className="space-y-2">
          <Label htmlFor="reranker-base-url">Base URL</Label>
          <Input
            id="reranker-base-url"
            value={rerankerBaseUrl}
            onChange={(e) => setRerankerBaseUrl(e.target.value)}
            placeholder="http://localhost:8080"
            aria-label="Reranker base URL"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="reranker-model">Model Name</Label>
          <Input
            id="reranker-model"
            value={rerankerModel}
            onChange={(e) => setRerankerModel(e.target.value)}
            placeholder="BAAI/bge-reranker-base"
            aria-label="Reranker model name"
          />
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
