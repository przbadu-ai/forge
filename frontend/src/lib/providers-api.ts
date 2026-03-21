import { apiFetch } from "@/lib/api";

export interface ProviderRead {
  id: number;
  name: string;
  base_url: string;
  models: string[];
  is_default: boolean;
  created_at: string;
}

export interface ProviderCreate {
  name: string;
  base_url: string;
  api_key?: string;
  models: string[];
  is_default?: boolean;
}

export interface ProviderUpdate {
  name?: string;
  base_url?: string;
  api_key?: string;
  models?: string[];
  is_default?: boolean;
}

export interface TestConnectionResult {
  ok: boolean;
  latency_ms?: number;
  model_count?: number;
  models?: string[];
  error?: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function listProviders(
  token: string
): Promise<ProviderRead[]> {
  const res = await apiFetch("/api/v1/settings/providers", token);
  return handleResponse<ProviderRead[]>(res);
}

export async function createProvider(
  token: string,
  data: ProviderCreate
): Promise<ProviderRead> {
  const res = await apiFetch("/api/v1/settings/providers", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return handleResponse<ProviderRead>(res);
}

export async function updateProvider(
  token: string,
  id: number,
  data: ProviderUpdate
): Promise<ProviderRead> {
  const res = await apiFetch(`/api/v1/settings/providers/${id}`, token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return handleResponse<ProviderRead>(res);
}

export async function deleteProvider(
  token: string,
  id: number
): Promise<void> {
  const res = await apiFetch(`/api/v1/settings/providers/${id}`, token, {
    method: "DELETE",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Delete failed (${res.status})`);
  }
}

export async function testConnection(
  token: string,
  base_url: string,
  api_key: string
): Promise<TestConnectionResult> {
  const res = await apiFetch(
    "/api/v1/settings/providers/test-connection",
    token,
    {
      method: "POST",
      body: JSON.stringify({ base_url, api_key }),
    }
  );
  return handleResponse<TestConnectionResult>(res);
}
