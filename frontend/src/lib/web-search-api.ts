import { apiFetch } from "@/lib/api";

export interface WebSearchSettings {
  searxng_base_url: string | null;
  exa_api_key_set: boolean;
}

export interface WebSearchSettingsUpdate {
  searxng_base_url?: string | null;
  exa_api_key?: string | null;
}

export async function getWebSearchSettings(
  token: string
): Promise<WebSearchSettings> {
  const res = await apiFetch("/api/v1/settings/web-search", token);
  if (!res.ok) throw new Error("Failed to fetch web search settings");
  return res.json() as Promise<WebSearchSettings>;
}

export async function updateWebSearchSettings(
  token: string,
  data: WebSearchSettingsUpdate
): Promise<WebSearchSettings> {
  const res = await apiFetch("/api/v1/settings/web-search", token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update web search settings");
  return res.json() as Promise<WebSearchSettings>;
}
