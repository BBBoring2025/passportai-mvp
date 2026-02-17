"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { getRole, clearAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";
import FileUploadZone from "@/components/ui/FileUploadZone";
import DocumentList from "@/components/ui/DocumentList";
import FieldCategoryAccordion from "@/components/ui/FieldCategoryAccordion";
import type { ExtractedField } from "@/components/ui/FieldCategoryAccordion";
import ChecklistSection from "@/components/ui/ChecklistSection";
import type { ChecklistItem } from "@/components/ui/ChecklistSection";

interface CaseDetail {
  id: string;
  reference_no: string;
  product_group: string;
  status: string;
  date_from: string | null;
  date_to: string | null;
  notes: string | null;
  document_count: number;
  created_at: string;
}

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

interface ProcessingResponse {
  case_id: string;
  documents_processed: number;
  documents_errored: number;
  case_status: string;
}

interface ExtractionResponse {
  document_id: string;
  fields_extracted: number;
  processing_status: string;
  token_usage: { input_tokens: number; output_tokens: number } | null;
}

export default function CaseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);
  const [processingResult, setProcessingResult] =
    useState<ProcessingResponse | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState("");
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([]);
  const [validating, setValidating] = useState(false);
  const [validationMessage, setValidationMessage] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [c, docs] = await Promise.all([
        apiFetch<CaseDetail>(`/cases/${caseId}`),
        apiFetch<DocumentItem[]>(`/cases/${caseId}/documents`),
      ]);
      setCaseData(c);
      setDocuments(docs);

      // Fetch fields if any docs are extracted
      const hasExtracted = docs.some(
        (d) => d.processing_status === "extracted"
      );
      if (hasExtracted) {
        try {
          const f = await apiFetch<ExtractedField[]>(
            `/cases/${caseId}/fields`
          );
          setFields(f);
        } catch {
          // Fields endpoint may fail if no fields yet
          setFields([]);
        }
      }

      // Fetch checklist items
      try {
        const cl = await apiFetch<ChecklistItem[]>(
          `/cases/${caseId}/checklist`
        );
        setChecklistItems(cl);
      } catch {
        setChecklistItems([]);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load case"
      );
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    const role = getRole();
    if (!role || role !== "supplier") {
      router.replace("/login");
      return;
    }
    fetchData();
  }, [router, caseId, fetchData]);

  const handleUploadComplete = useCallback(() => {
    apiFetch<DocumentItem[]>(`/cases/${caseId}/documents`).then(
      setDocuments
    );
    apiFetch<CaseDetail>(`/cases/${caseId}`).then(setCaseData);
  }, [caseId]);

  const handleStartProcessing = useCallback(async () => {
    setProcessing(true);
    setError("");
    setProcessingResult(null);

    try {
      const result = await apiFetch<ProcessingResponse>(
        `/cases/${caseId}/start-processing`,
        { method: "POST" }
      );
      setProcessingResult(result);

      // Refresh data to show updated statuses
      const [c, docs] = await Promise.all([
        apiFetch<CaseDetail>(`/cases/${caseId}`),
        apiFetch<DocumentItem[]>(`/cases/${caseId}/documents`),
      ]);
      setCaseData(c);
      setDocuments(docs);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Islem basarisiz oldu"
      );
    } finally {
      setProcessing(false);
    }
  }, [caseId]);

  const handleRetry = useCallback(
    async (documentId: string) => {
      try {
        await apiFetch<ProcessingResponse>(
          `/documents/${documentId}/retry`,
          { method: "POST" }
        );
        // Refresh data
        const [c, docs] = await Promise.all([
          apiFetch<CaseDetail>(`/cases/${caseId}`),
          apiFetch<DocumentItem[]>(`/cases/${caseId}/documents`),
        ]);
        setCaseData(c);
        setDocuments(docs);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Tekrar deneme basarisiz oldu"
        );
      }
    },
    [caseId]
  );

  const handleStartExtraction = useCallback(async () => {
    setExtracting(true);
    setError("");
    setExtractionProgress("");

    const classifiedDocs = documents.filter(
      (d) =>
        d.processing_status === "classified" && d.doc_type
    );

    let total = 0;
    let errors = 0;

    for (let i = 0; i < classifiedDocs.length; i++) {
      const doc = classifiedDocs[i];
      setExtractionProgress(
        `${i + 1}/${classifiedDocs.length}: ${doc.original_filename}`
      );

      try {
        const result = await apiFetch<ExtractionResponse>(
          `/documents/${doc.id}/run-extraction`,
          { method: "POST" }
        );
        total += result.fields_extracted;
      } catch (err) {
        errors++;
        console.error(
          `Extraction failed for ${doc.original_filename}:`,
          err
        );
      }
    }

    setExtractionProgress(
      `Tamamlandi: ${total} alan cikarildi` +
        (errors > 0 ? `, ${errors} hatali` : "")
    );

    // Refresh all data
    try {
      const [c, docs, f] = await Promise.all([
        apiFetch<CaseDetail>(`/cases/${caseId}`),
        apiFetch<DocumentItem[]>(`/cases/${caseId}/documents`),
        apiFetch<ExtractedField[]>(`/cases/${caseId}/fields`),
      ]);
      setCaseData(c);
      setDocuments(docs);
      setFields(f);
    } catch {
      // Partial refresh is OK
    }

    setExtracting(false);
  }, [caseId, documents]);

  const handleViewEvidence = useCallback(
    (documentId: string, page: number, snippet: string) => {
      const params = new URLSearchParams({
        doc: documentId,
        page: String(page),
        snippet,
      });
      router.push(
        `/supplier/cases/${caseId}/viewer?${params.toString()}`
      );
    },
    [caseId, router]
  );

  const handleRunValidation = useCallback(async () => {
    setValidating(true);
    setValidationMessage("");
    setError("");

    try {
      const result = await apiFetch<{
        total_rules: number;
        passed: number;
        failed: number;
        warnings: number;
        checklist_items_created: number;
      }>(`/cases/${caseId}/run-validation`, { method: "POST" });

      setValidationMessage(
        `Validasyon tamamlandi: ${result.passed} gecti, ${result.failed} basarisiz, ${result.warnings} uyari. ` +
          `${result.checklist_items_created} kontrol maddesi olusturuldu.`
      );

      // Refresh checklist
      try {
        const cl = await apiFetch<ChecklistItem[]>(
          `/cases/${caseId}/checklist`
        );
        setChecklistItems(cl);
      } catch {
        // ignore
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Validasyon basarisiz oldu"
      );
    } finally {
      setValidating(false);
    }
  }, [caseId]);

  // Determine UI states
  const hasUploadedDocs = documents.some(
    (d) => d.processing_status === "uploaded"
  );
  const hasClassifiedDocs = documents.some(
    (d) =>
      d.processing_status === "classified" && d.doc_type
  );
  const hasExtractedDocs = documents.some(
    (d) => d.processing_status === "extracted"
  );
  const UPLOAD_ALLOWED = ["draft", "blocked", "ready_l1", "ready_l2"];
  const canUpload = caseData?.status
    ? UPLOAD_ALLOWED.includes(caseData.status)
    : false;

  if (loading) {
    return (
      <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
        <div className="max-w-4xl mx-auto">
          <p className="text-gray-500 text-center py-12">
            Yukleniyor...
          </p>
        </div>
      </div>
    );
  }

  if (error && !caseData) {
    return (
      <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
        <div className="max-w-4xl mx-auto">
          <div className="p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-700 dark:text-red-400">
              {error || "Case not found"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!caseData) return null;

  return (
    <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <button
              onClick={() => router.push("/supplier/cases")}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2 flex items-center gap-1"
            >
              &larr; Paketlerim
            </button>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">
                {caseData.reference_no}
              </h1>
              <StatusBadge status={caseData.status} />
            </div>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span>{caseData.product_group}</span>
              {caseData.date_from && (
                <span>
                  {caseData.date_from}
                  {caseData.date_to
                    ? ` — ${caseData.date_to}`
                    : ""}
                </span>
              )}
              <span>
                {new Date(caseData.created_at).toLocaleDateString(
                  "tr-TR"
                )}
              </span>
            </div>
            {caseData.notes && (
              <p className="text-sm text-gray-500 mt-2">
                {caseData.notes}
              </p>
            )}
          </div>

          <button
            onClick={() => {
              clearAuth();
              router.push("/login");
            }}
            className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            Sign out
          </button>
        </div>

        {/* Upload Zone — show for draft, blocked, ready_l1, ready_l2 */}
        {canUpload && (
          <FileUploadZone
            caseId={caseId}
            onUploadComplete={handleUploadComplete}
          />
        )}

        {/* Document List */}
        <DocumentList
          documents={documents}
          onRetry={handleRetry}
        />

        {/* Error message */}
        {error && (
          <div className="mt-4 p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-700 dark:text-red-400">
              {error}
            </p>
          </div>
        )}

        {/* Processing result summary */}
        {processingResult && (
          <div className="mt-4 p-3 rounded bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-700 dark:text-blue-400">
              {processingResult.documents_processed} dosya
              islendi
              {processingResult.documents_errored > 0 &&
                `, ${processingResult.documents_errored} hatali`}
            </p>
          </div>
        )}

        {/* Extraction progress */}
        {extractionProgress && (
          <div className="mt-4 p-3 rounded bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800">
            <p className="text-sm text-indigo-700 dark:text-indigo-400">
              {extractionProgress}
            </p>
          </div>
        )}

        {/* Extracted Fields Section */}
        {(hasExtractedDocs || fields.length > 0) && (
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Cikarilan Alanlar ({fields.length})
            </h3>
            <FieldCategoryAccordion
              fields={fields}
              onViewEvidence={handleViewEvidence}
            />
          </div>
        )}

        {/* Validation message */}
        {validationMessage && (
          <div className="mt-4 p-3 rounded bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
            <p className="text-sm text-purple-700 dark:text-purple-400">
              {validationMessage}
            </p>
          </div>
        )}

        {/* Checklist Section */}
        {(checklistItems.length > 0 || hasExtractedDocs) && (
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Kontrol Listesi ({checklistItems.filter((i) => i.status !== "done").length} acik)
            </h3>
            <ChecklistSection
              items={checklistItems}
              onItemUpdate={fetchData}
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex justify-end gap-3">
          {hasUploadedDocs && (
            <button
              onClick={handleStartProcessing}
              disabled={processing || !hasUploadedDocs}
              className="px-6 py-3 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {processing
                ? "Isleniyor..."
                : "Islemeyi Baslat"}
            </button>
          )}

          {hasClassifiedDocs && !extracting && (
            <button
              onClick={handleStartExtraction}
              disabled={extracting}
              className="px-6 py-3 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              AI Cikarma Baslat
            </button>
          )}

          {extracting && (
            <button
              disabled
              className="px-6 py-3 rounded-lg bg-indigo-600 text-white font-medium opacity-60 cursor-not-allowed flex items-center gap-2"
            >
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              Cikariliyor...
            </button>
          )}

          {hasExtractedDocs && !validating && (
            <button
              onClick={handleRunValidation}
              disabled={validating}
              className="px-6 py-3 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Validasyonu Calistir
            </button>
          )}

          {validating && (
            <button
              disabled
              className="px-6 py-3 rounded-lg bg-purple-600 text-white font-medium opacity-60 cursor-not-allowed flex items-center gap-2"
            >
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              Dogrulaniyor...
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
