"use client";

import StatusBadge from "./StatusBadge";

interface DocumentItem {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  page_count: number | null;
  doc_type: string | null;
  classification_method: string | null;
  classification_confidence: number | null;
  processing_status: string;
  error_code: string | null;
  error_message: string | null;
  sha256_hash: string | null;
  created_at: string;
}

interface DocumentListProps {
  documents: DocumentItem[];
  onRetry?: (documentId: string) => void;
}

// English labels for doc_type
const DOC_TYPE_LABELS: Record<string, string> = {
  invoice: "Invoice",
  packing_list: "Packing List",
  certificate: "Certificate",
  test_report: "Test Report",
  sds: "SDS",
  bom: "BOM",
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function mimeIcon(mime: string): string {
  if (mime === "application/pdf") return "PDF";
  if (mime.startsWith("image/")) return "IMG";
  return "DOC";
}

export default function DocumentList({ documents, onRetry }: DocumentListProps) {
  if (documents.length === 0) {
    return null;
  }

  return (
    <div className="mt-6">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        Uploaded Files ({documents.length})
      </h3>
      <div className="space-y-2">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className={`p-3 rounded-lg border bg-white dark:bg-gray-800/50 ${
              doc.processing_status === "error"
                ? "border-red-300 dark:border-red-700"
                : "border-gray-200 dark:border-gray-700"
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono font-bold text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {mimeIcon(doc.mime_type)}
              </span>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {doc.original_filename}
                </p>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  <span className="text-xs text-gray-500">
                    {formatFileSize(doc.file_size_bytes)}
                  </span>
                  {doc.doc_type && (
                    <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                      {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type.replace("_", " ")}
                    </span>
                  )}
                  {doc.classification_method && (
                    <span className="text-xs text-gray-400">
                      ({doc.classification_method})
                    </span>
                  )}
                  {doc.page_count != null && (
                    <span className="text-xs text-gray-400">
                      {doc.page_count} pages
                    </span>
                  )}
                  {doc.sha256_hash && (
                    <span
                      className="text-xs text-gray-400 font-mono"
                      title={doc.sha256_hash}
                    >
                      #{doc.sha256_hash.slice(0, 8)}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {doc.processing_status === "error" && onRetry && (
                  <button
                    onClick={() => onRetry(doc.id)}
                    className="text-xs px-2 py-1 rounded bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50"
                  >
                    Retry
                  </button>
                )}
                <StatusBadge status={doc.processing_status} />
              </div>
            </div>

            {/* Error message */}
            {doc.processing_status === "error" && doc.error_message && (
              <div className="mt-2 ml-10 p-2 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                <p className="text-xs text-red-700 dark:text-red-400">
                  {doc.error_message}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
