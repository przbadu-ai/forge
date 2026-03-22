import { apiFetch } from "@/lib/api";
import type { GeneralSettings } from "@/types/chat";

export async function getGeneralSettings(
  token: string
): Promise<GeneralSettings> {
  const res = await apiFetch("/api/v1/settings/general", token);
  if (!res.ok) throw new Error("Failed to fetch general settings");
  return res.json() as Promise<GeneralSettings>;
}

export async function updateGeneralSettings(
  token: string,
  data: Partial<GeneralSettings>
): Promise<GeneralSettings> {
  const res = await apiFetch("/api/v1/settings/general", token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update general settings");
  return res.json() as Promise<GeneralSettings>;
}
