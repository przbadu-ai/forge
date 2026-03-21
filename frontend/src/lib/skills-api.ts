import { apiFetch } from "@/lib/api";

export interface SkillRead {
  id: number;
  name: string;
  description: string;
  is_enabled: boolean;
  config: string | null;
  created_at: string;
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
