import { apiFetch } from "@/lib/api";

export type McpTransportType = "stdio" | "sse" | "streamable_http";

export interface McpServerRead {
  id: number;
  name: string;
  command: string | null;
  args: string[];
  env_vars: Record<string, string>;
  is_enabled: boolean;
  transport_type: McpTransportType;
  url: string | null;
  created_at: string;
}

export interface McpServerCreate {
  name: string;
  command?: string | null;
  args?: string[];
  env_vars?: Record<string, string>;
  is_enabled?: boolean;
  transport_type?: McpTransportType;
  url?: string | null;
}

export interface McpServerUpdate {
  name?: string;
  command?: string | null;
  args?: string[];
  env_vars?: Record<string, string>;
  is_enabled?: boolean;
  transport_type?: McpTransportType;
  url?: string | null;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    let message: string;
    if (Array.isArray(body.detail)) {
      // FastAPI validation errors: [{loc: [...], msg: "...", type: "..."}, ...]
      message = body.detail
        .map((e: Record<string, unknown>) => {
          const loc = Array.isArray(e.loc) ? e.loc.join(" > ") : "";
          return loc ? `${loc}: ${e.msg}` : String(e.msg ?? e);
        })
        .join("; ");
    } else if (typeof body.detail === "string") {
      message = body.detail;
    } else {
      message = `Request failed (${res.status})`;
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function listMcpServers(token: string): Promise<McpServerRead[]> {
  const res = await apiFetch("/api/v1/settings/mcp-servers", token);
  return handleResponse<McpServerRead[]>(res);
}

export async function createMcpServer(
  token: string,
  data: McpServerCreate
): Promise<McpServerRead> {
  const res = await apiFetch("/api/v1/settings/mcp-servers", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return handleResponse<McpServerRead>(res);
}

export async function updateMcpServer(
  token: string,
  id: number,
  data: McpServerUpdate
): Promise<McpServerRead> {
  const res = await apiFetch(`/api/v1/settings/mcp-servers/${id}`, token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return handleResponse<McpServerRead>(res);
}

export async function deleteMcpServer(
  token: string,
  id: number
): Promise<void> {
  const res = await apiFetch(`/api/v1/settings/mcp-servers/${id}`, token, {
    method: "DELETE",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Delete failed (${res.status})`);
  }
}

export async function toggleMcpServer(
  token: string,
  id: number
): Promise<McpServerRead> {
  const res = await apiFetch(
    `/api/v1/settings/mcp-servers/${id}/toggle`,
    token,
    { method: "PATCH" }
  );
  return handleResponse<McpServerRead>(res);
}

export interface McpBulkImportResponse {
  created: number;
  updated: number;
  servers: McpServerRead[];
}

export async function importMcpServers(
  token: string,
  data: {
    mcpServers: Record<
      string,
      {
        command?: string;
        args?: string[];
        env?: Record<string, string>;
        url?: string;
      }
    >;
  }
): Promise<McpBulkImportResponse> {
  const res = await apiFetch("/api/v1/settings/mcp-servers/import", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return handleResponse<McpBulkImportResponse>(res);
}
