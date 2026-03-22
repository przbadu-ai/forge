"use client";

import { useCallback, useRef, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { uploadFile } from "@/lib/files-api";
import { Button } from "@/components/ui/button";
import { Upload, Loader2 } from "lucide-react";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "text/markdown",
];

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.md";

interface FileUploadProps {
  onUploadComplete?: () => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const { token } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleUpload = useCallback(
    async (file: File) => {
      if (!token) return;

      setError(null);
      setUploading(true);

      try {
        await uploadFile(token, file);
        onUploadComplete?.();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [token, onUploadComplete]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) void handleUpload(file);
      // Reset input so same file can be re-uploaded
      if (inputRef.current) inputRef.current.value = "";
    },
    [handleUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        const ext = file.name.toLowerCase().split(".").pop();
        if (
          ACCEPTED_TYPES.includes(file.type) ||
          ["pdf", "docx", "txt", "md"].includes(ext ?? "")
        ) {
          void handleUpload(file);
        } else {
          setError("Unsupported file type. Accepted: PDF, DOCX, TXT, MD");
        }
      }
    },
    [handleUpload]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  return (
    <div className="space-y-2">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
          dragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50"
        }`}
      >
        {uploading ? (
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="text-muted-foreground h-8 w-8 animate-spin" />
            <p className="text-muted-foreground text-sm">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Upload className="text-muted-foreground h-8 w-8" />
            <p className="text-muted-foreground text-sm">
              Drag and drop a file, or click to browse
            </p>
            <p className="text-muted-foreground text-xs">
              Supported: PDF, DOCX, TXT, MD (max 50 MB)
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
            >
              Choose File
            </Button>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleFileChange}
          className="hidden"
          aria-label="Upload file"
        />
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}
    </div>
  );
}
