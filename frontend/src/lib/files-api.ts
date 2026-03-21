const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface UploadedFile {
  id: number;
  filename: string;
  original_name: string;
  content_type: string;
  size_bytes: number;
  status: "pending" | "processing" | "ready" | "failed";
  chunk_count: number;
  user_id: number;
  created_at: string;
}

export interface FileUploadResponse {
  id: number;
  original_name: string;
  status: string;
  message: string;
}

export async function uploadFile(
  token: string,
  file: File,
): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/v1/files/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    credentials: "include",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(
      (body as { detail?: string }).detail ?? "Failed to upload file",
    );
  }

  return res.json() as Promise<FileUploadResponse>;
}

export async function listFiles(token: string): Promise<UploadedFile[]> {
  const res = await fetch(`${API_BASE}/api/v1/files/`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!res.ok) throw new Error("Failed to list files");
  return res.json() as Promise<UploadedFile[]>;
}

export async function getFile(
  token: string,
  fileId: number,
): Promise<UploadedFile> {
  const res = await fetch(`${API_BASE}/api/v1/files/${fileId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!res.ok) throw new Error("Failed to get file");
  return res.json() as Promise<UploadedFile>;
}

export async function deleteFile(
  token: string,
  fileId: number,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/files/${fileId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!res.ok) throw new Error("Failed to delete file");
}
