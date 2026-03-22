import { apiFetch } from "@/lib/api";

export interface EmbeddingSettings {
  embedding_base_url: string | null;
  embedding_model: string | null;
  reranker_base_url: string | null;
  reranker_model: string | null;
}

export async function getEmbeddingSettings(
  token: string
): Promise<EmbeddingSettings> {
  const res = await apiFetch("/api/v1/settings/embeddings", token);
  if (!res.ok) throw new Error("Failed to fetch embedding settings");
  return res.json() as Promise<EmbeddingSettings>;
}

export async function updateEmbeddingSettings(
  token: string,
  data: Partial<EmbeddingSettings>
): Promise<EmbeddingSettings> {
  const res = await apiFetch("/api/v1/settings/embeddings", token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update embedding settings");
  return res.json() as Promise<EmbeddingSettings>;
}
