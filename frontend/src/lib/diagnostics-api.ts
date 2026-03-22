import { apiFetch } from "@/lib/api";

export interface ServiceStatus {
  name: string;
  status: "ok" | "error" | "unconfigured";
  latency_ms: number | null;
  error: string | null;
}

export interface DiagnosticsResponse {
  services: ServiceStatus[];
}

export async function getDiagnostics(
  token: string
): Promise<DiagnosticsResponse> {
  const res = await apiFetch("/api/v1/diagnostics", token);
  if (!res.ok) throw new Error("Failed to fetch diagnostics");
  return res.json() as Promise<DiagnosticsResponse>;
}
