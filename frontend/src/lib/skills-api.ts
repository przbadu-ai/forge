import { apiFetch } from "@/lib/api";

export interface SkillRead {
  id: number;
  name: string;
  description: string;
  is_enabled: boolean;
  config: string | null;
  source_path: string | null;
  instructions: string | null;
  created_at: string;
}

export interface SkillCreate {
  name: string;
  description: string;
  is_enabled?: boolean;
}

export interface SkillUpdate {
  name?: string;
  description?: string;
  is_enabled?: boolean;
}

export interface SyncResult {
  created: number;
  updated: number;
  total_discovered: number;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function listSkills(token: string): Promise<SkillRead[]> {
  const res = await apiFetch("/api/v1/settings/skills/", token);
  return handleResponse<SkillRead[]>(res);
}

export async function toggleSkill(
  token: string,
  id: number
): Promise<SkillRead> {
  const res = await apiFetch(`/api/v1/settings/skills/${id}/toggle`, token, {
    method: "PATCH",
  });
  return handleResponse<SkillRead>(res);
}

export async function createSkill(
  token: string,
  data: SkillCreate
): Promise<SkillRead> {
  const res = await apiFetch("/api/v1/settings/skills/", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return handleResponse<SkillRead>(res);
}

export async function updateSkill(
  token: string,
  id: number,
  data: SkillUpdate
): Promise<SkillRead> {
  const res = await apiFetch(`/api/v1/settings/skills/${id}`, token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return handleResponse<SkillRead>(res);
}

export async function deleteSkill(
  token: string,
  id: number
): Promise<void> {
  const res = await apiFetch(`/api/v1/settings/skills/${id}`, token, {
    method: "DELETE",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
}

export async function syncSkills(token: string): Promise<SyncResult> {
  const res = await apiFetch("/api/v1/settings/skills/sync", token, {
    method: "POST",
  });
  return handleResponse<SyncResult>(res);
}
