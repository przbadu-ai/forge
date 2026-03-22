"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { listFiles, deleteFile } from "@/lib/files-api";
import type { UploadedFile } from "@/lib/files-api";
import { Button } from "@/components/ui/button";
import { FileUpload } from "@/components/chat/file-upload";
import {
  Trash2,
  FileText,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
} from "lucide-react";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "ready":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-400">
          <CheckCircle className="h-3 w-3" />
          Ready
        </span>
      );
    case "processing":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
          <Loader2 className="h-3 w-3 animate-spin" />
          Processing
        </span>
      );
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700 dark:bg-red-900/30 dark:text-red-400">
          <AlertCircle className="h-3 w-3" />
          Failed
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-900/30 dark:text-gray-400">
          <Clock className="h-3 w-3" />
          Pending
        </span>
      );
  }
}

export function FileList() {
  const { token } = useAuth();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchFiles = useCallback(async () => {
    if (!token) return;
    try {
      const result = await listFiles(token);
      setFiles(result);
    } catch {
      // Silently handle — files list failure is non-critical
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void fetchFiles();
  }, [fetchFiles]);

  // Poll for status updates when there are processing files
  useEffect(() => {
    const hasProcessing = files.some(
      (f) => f.status === "pending" || f.status === "processing"
    );
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      void fetchFiles();
    }, 3000);

    return () => clearInterval(interval);
  }, [files, fetchFiles]);

  const handleDelete = useCallback(
    async (fileId: number) => {
      if (!token) return;
      setDeletingId(fileId);
      try {
        await deleteFile(token, fileId);
        setFiles((prev) => prev.filter((f) => f.id !== fileId));
      } catch {
        // Delete failed
      } finally {
        setDeletingId(null);
      }
    },
    [token]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <FileUpload onUploadComplete={() => void fetchFiles()} />

      {files.length === 0 ? (
        <p className="text-muted-foreground py-8 text-center text-sm">
          No files uploaded yet. Upload a document to enable RAG-based Q&A.
        </p>
      ) : (
        <div className="space-y-2">
          {files.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between rounded-lg border p-3"
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <FileText className="text-muted-foreground h-5 w-5 shrink-0" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">
                    {file.original_name}
                  </p>
                  <p className="text-muted-foreground text-xs">
                    {formatSize(file.size_bytes)}
                    {file.chunk_count > 0 &&
                      ` \u00b7 ${file.chunk_count} chunks`}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={file.status} />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => void handleDelete(file.id)}
                  disabled={deletingId === file.id}
                  aria-label={`Delete ${file.original_name}`}
                >
                  {deletingId === file.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
