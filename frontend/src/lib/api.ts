// apiFetch wraps fetch with Authorization header injection.
// Token is passed in explicitly (consumers get it from useAuth).
// Production: NEXT_PUBLIC_API_URL="" (empty) → same origin via Next.js rewrites.
// Development: NEXT_PUBLIC_API_URL unset → fallback to hostname:8000 for direct access.
function getApiBase(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  // Explicitly set (even to empty string) — use it. Empty = same origin (reverse proxy/rewrites).
  if (envUrl !== undefined && envUrl !== null) return envUrl;
  // Development fallback: use backend port on same hostname (enables LAN access)
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
}

export const API_BASE = getApiBase();

export async function apiFetch(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
  });
}
