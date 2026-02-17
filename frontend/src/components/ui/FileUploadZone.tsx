"use client";

import { useCallback, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";

interface DocumentUploadResponse {
  document_id: string;
  status: string;
  sha256_hash: string;
}

interface FileUploadZoneProps {
  caseId: string;
  onUploadComplete: () => void;
}

export default function FileUploadZone({
  caseId,
  onUploadComplete,
}: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [uploadCount, setUploadCount] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const ACCEPTED = ".pdf,.jpg,.jpeg,.png";

  const uploadFiles = useCallback(
    async (files: FileList | File[]) => {
      setError("");
      setUploading(true);
      setUploadCount(0);

      const fileArray = Array.from(files);
      let successCount = 0;

      for (const file of fileArray) {
        try {
          const formData = new FormData();
          formData.append("case_id", caseId);
          formData.append("file", file);

          await apiFetch<DocumentUploadResponse>("/documents", {
            method: "POST",
            body: formData,
          });

          successCount++;
          setUploadCount(successCount);
        } catch (err) {
          setError(
            err instanceof Error
              ? err.message
              : `Failed to upload ${file.name}`
          );
        }
      }

      setUploading(false);
      if (successCount > 0) {
        onUploadComplete();
      }
    },
    [caseId, onUploadComplete]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!uploading) setIsDragging(true);
    },
    [uploading]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      if (!uploading && e.dataTransfer.files.length > 0) {
        uploadFiles(e.dataTransfer.files);
      }
    },
    [uploading, uploadFiles]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        uploadFiles(e.target.files);
        e.target.value = "";
      }
    },
    [uploadFiles]
  );

  return (
    <div>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-colors duration-200
          ${
            isDragging
              ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
              : "border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500"
          }
          ${uploading ? "opacity-60 cursor-wait" : ""}
        `}
      >
        <div className="text-4xl mb-4">
          {uploading ? "⏳" : "📄"}
        </div>

        {uploading ? (
          <div>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              Yukleniyor... ({uploadCount} tamamlandi)
            </p>
          </div>
        ) : (
          <div>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              Dosyalari buraya surukleyin
            </p>
            <p className="text-sm text-gray-500 mt-1">
              veya secmek icin tiklayin
            </p>
            <p className="text-xs text-gray-400 mt-2">
              PDF, JPG, PNG &bull; Maks. 50 MB
            </p>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED}
          multiple
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* Mobile camera button */}
      <div className="mt-3 sm:hidden">
        <button
          type="button"
          onClick={() => cameraInputRef.current?.click()}
          disabled={uploading}
          className="w-full py-3 px-4 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          Fotograf Cek
        </button>
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/jpeg,image/png"
          capture="environment"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {error && (
        <div className="mt-3 p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}
    </div>
  );
}
