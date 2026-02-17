"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { getRole } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";
import type { ExtractedField } from "@/components/ui/FieldCategoryAccordion";

// Turkish labels for canonical keys
const FIELD_LABELS: Record<string, string> = {
  "shipment.invoice_number": "Fatura Numarasi",
  "shipment.invoice_date": "Fatura Tarihi",
  "shipment.total_quantity": "Toplam Miktar",
  "shipment.unit": "Birim",
  "customs.hs_code": "HS Kodu",
  "product.sku": "Urun Kodu (SKU)",
  "product.name": "Urun Adi",
  "factory.country": "Fabrika Ulkesi",
  "factory.name": "Fabrika Adi",
  "shipment.packing_list_number": "Ambalaj Listesi No",
  "certificate.oekotex.number": "OEKO-TEX Sertifika No",
  "certificate.oekotex.valid_until": "Gecerlilik Tarihi",
  "certificate.issuer": "Sertifika Veren Kurum",
  "test_report.lab_name": "Laboratuvar Adi",
  "test_report.report_number": "Rapor Numarasi",
  "test_report.report_date": "Rapor Tarihi",
  "test_report.result_pass_fail": "Sonuc (Gecti/Kaldi)",
  "material.composition.cotton_pct": "Pamuk Orani (%)",
  "material.composition.elastane_pct": "Elastan Orani (%)",
  "material.composition.total_pct": "Toplam Oran (%)",
  "sds.exists": "SDS Mevcut",
  "chemical.restricted_substances_pass_fail": "Kisitli Madde Sonucu",
  "batch.id": "Parti Numarasi",
  "batch.production_date_from": "Uretim Baslangic",
  "batch.production_date_to": "Uretim Bitis",
};

interface PageData {
  page_number: number;
  total_pages: number;
  text: string;
  extraction_method: string;
}

export default function DocumentViewerPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();

  const caseId = params.id as string;
  const docId = searchParams.get("doc") || "";
  const initialPage = parseInt(searchParams.get("page") || "1", 10);
  const highlightSnippet = searchParams.get("snippet") || "";

  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageData, setPageData] = useState<PageData | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeSnippet, setActiveSnippet] = useState(highlightSnippet);

  const fetchPage = useCallback(
    async (pageNum: number) => {
      if (!docId) return;
      try {
        const data = await apiFetch<PageData>(
          `/documents/${docId}/render?page=${pageNum}`
        );
        setPageData(data);
        setCurrentPage(pageNum);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Sayfa yuklenemedi"
        );
      }
    },
    [docId]
  );

  const fetchFields = useCallback(async () => {
    try {
      const allFields = await apiFetch<ExtractedField[]>(
        `/cases/${caseId}/fields`
      );
      // Filter to this document
      setFields(allFields.filter((f) => f.document_id === docId));
    } catch {
      setFields([]);
    }
  }, [caseId, docId]);

  useEffect(() => {
    const role = getRole();
    if (!role || role !== "supplier") {
      router.replace("/login");
      return;
    }
    if (!docId) {
      setError("Dokuman ID belirtilmedi");
      setLoading(false);
      return;
    }

    Promise.all([fetchPage(initialPage), fetchFields()]).then(() =>
      setLoading(false)
    );
  }, [router, docId, initialPage, fetchPage, fetchFields]);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      fetchPage(currentPage - 1);
      setActiveSnippet("");
    }
  };

  const handleNextPage = () => {
    if (pageData && currentPage < pageData.total_pages) {
      fetchPage(currentPage + 1);
      setActiveSnippet("");
    }
  };

  const handleFieldClick = (field: ExtractedField) => {
    setActiveSnippet(field.snippet);
    if (field.page !== currentPage) {
      fetchPage(field.page);
    }
  };

  // Highlight snippet in page text
  const renderPageText = () => {
    if (!pageData) return null;
    const text = pageData.text;

    if (!activeSnippet || !text.includes(activeSnippet)) {
      return (
        <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
          {text}
        </pre>
      );
    }

    const parts = text.split(activeSnippet);
    return (
      <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
        {parts.map((part, i) => (
          <span key={i}>
            {part}
            {i < parts.length - 1 && (
              <mark className="bg-yellow-200 dark:bg-yellow-800 px-0.5 rounded">
                {activeSnippet}
              </mark>
            )}
          </span>
        ))}
      </pre>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
        <p className="text-gray-500 text-center py-12">
          Yukleniyor...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen font-[family-name:var(--font-geist-sans)]">
      {/* Top bar */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between bg-white dark:bg-gray-900">
        <button
          onClick={() =>
            router.push(`/supplier/cases/${caseId}`)
          }
          className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1"
        >
          &larr; Pakete Don
        </button>
        <div className="text-sm text-gray-500">
          Dokuman Goruntuleyici
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-700 dark:text-red-400">
            {error}
          </p>
        </div>
      )}

      {/* 2-panel layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 h-[calc(100vh-57px)]">
        {/* Left panel — Page text viewer */}
        <div className="border-r border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
          {/* Page navigation */}
          <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50">
            <button
              onClick={handlePrevPage}
              disabled={currentPage <= 1}
              className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              &larr; Onceki
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Sayfa {currentPage} / {pageData?.total_pages || "?"}
            </span>
            <button
              onClick={handleNextPage}
              disabled={
                !pageData ||
                currentPage >= pageData.total_pages
              }
              className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              Sonraki &rarr;
            </button>
          </div>

          {/* Page content */}
          <div className="flex-1 overflow-auto p-4 bg-white dark:bg-gray-900">
            {pageData ? (
              renderPageText()
            ) : (
              <p className="text-gray-400 text-center py-8">
                Sayfa yuklenemedi
              </p>
            )}
          </div>

          {/* Extraction method indicator */}
          {pageData && (
            <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <span className="text-xs text-gray-400">
                Cikarma yontemi: {pageData.extraction_method}
              </span>
            </div>
          )}
        </div>

        {/* Right panel — Extracted fields */}
        <div className="flex flex-col overflow-hidden">
          <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              Cikarilan Alanlar ({fields.length})
            </h3>
          </div>

          <div className="flex-1 overflow-auto">
            {fields.length === 0 ? (
              <p className="text-gray-400 text-center py-8 text-sm">
                Bu dokuman icin cikarilmis alan yok
              </p>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {fields.map((field) => (
                  <div
                    key={field.id}
                    className={`px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/30 cursor-pointer transition-colors ${
                      activeSnippet === field.snippet
                        ? "bg-yellow-50 dark:bg-yellow-900/10 border-l-2 border-yellow-400"
                        : ""
                    }`}
                    onClick={() => handleFieldClick(field)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">
                        {FIELD_LABELS[field.canonical_key] ||
                          field.canonical_key}
                      </span>
                      <div className="flex items-center gap-2">
                        {field.confidence != null && (
                          <span className="text-xs text-gray-400 tabular-nums">
                            {Math.round(
                              field.confidence * 100
                            )}
                            %
                          </span>
                        )}
                        <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                          {field.tier}
                        </span>
                        <StatusBadge
                          status={field.status}
                        />
                      </div>
                    </div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {field.value}
                      {field.unit && (
                        <span className="text-gray-500 ml-1">
                          {field.unit}
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-gray-400 mt-1 truncate">
                      S.{field.page}: &quot;{field.snippet}&quot;
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
