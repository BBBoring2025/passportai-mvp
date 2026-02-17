"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getRole, clearAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";
import FieldCategoryAccordion from "@/components/ui/FieldCategoryAccordion";
import type { ExtractedField } from "@/components/ui/FieldCategoryAccordion";

interface CaseDetail {
  id: string;
  reference_no: string;
  product_group: string;
  status: string;
  created_at: string;
}

interface CaseMetrics {
  case_id: string;
  evidence_coverage_pct: number;
  conflict_rate: number;
  days_to_ready_l1: number | null;
  days_to_ready_l2: number | null;
  total_fields: number;
  l1_fields: number;
  l2_fields: number;
  buyer_visible_fields: number;
  required_fields_present: number;
  required_fields_total: number;
  checklist_open: number;
  checklist_done: number;
}

function coverageColor(pct: number): string {
  if (pct >= 80) return "text-green-600 dark:text-green-400";
  if (pct >= 50) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
}

export default function BuyerSupplierDetailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const caseId = searchParams.get("case");

  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [metrics, setMetrics] = useState<CaseMetrics | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const role = getRole();
    if (!role || (role !== "buyer" && role !== "admin")) {
      router.replace("/login");
    }
  }, [router]);

  const fetchData = useCallback(async () => {
    if (!caseId) {
      setError("Case ID belirtilmedi");
      setLoading(false);
      return;
    }

    try {
      const [c, m, f] = await Promise.all([
        apiFetch<CaseDetail>(`/cases/${caseId}`),
        apiFetch<CaseMetrics>(`/cases/${caseId}/metrics`),
        apiFetch<ExtractedField[]>(`/cases/${caseId}/fields`),
      ]);
      setCaseData(c);
      setMetrics(m);
      setFields(f);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Veri yuklenemedi"
      );
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDownloadReport = async () => {
    if (!caseId) return;
    setDownloading(true);
    try {
      const report = await apiFetch<Record<string, unknown>>(
        `/reports/case/${caseId}`
      );
      const blob = new Blob(
        [JSON.stringify(report, null, 2)],
        { type: "application/json" }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `readiness-report-${caseData?.reference_no || caseId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Rapor indirilemedi"
      );
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
        <div className="max-w-4xl mx-auto">
          <p className="text-gray-500 text-center py-12">Yukleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <button
              onClick={() => router.push("/buyer/dashboard")}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2 flex items-center gap-1"
            >
              &larr; Dashboard
            </button>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">
                Tedarikci Detay
              </h1>
              {caseData && <StatusBadge status={caseData.status} />}
            </div>
            {caseData && (
              <p className="text-sm text-gray-500 mt-1">
                Paket: {caseData.reference_no} | {caseData.product_group} |{" "}
                {new Date(caseData.created_at).toLocaleDateString("tr-TR")}
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

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Metrics Row */}
        {metrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Kapsam
              </p>
              <p className={`text-2xl font-bold mt-1 ${coverageColor(metrics.evidence_coverage_pct)}`}>
                %{metrics.evidence_coverage_pct.toFixed(1)}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {metrics.required_fields_present}/{metrics.required_fields_total} zorunlu alan
              </p>
            </div>
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Cakisma Orani
              </p>
              <p className="text-2xl font-bold mt-1">
                %{metrics.conflict_rate.toFixed(1)}
              </p>
            </div>
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Alanlar (L1/L2)
              </p>
              <p className="text-2xl font-bold mt-1">
                {metrics.l1_fields} / {metrics.l2_fields}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {metrics.buyer_visible_fields} alici gorunur
              </p>
            </div>
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Kontrol Listesi
              </p>
              <p className="text-2xl font-bold mt-1">
                {metrics.checklist_done}/{metrics.checklist_open + metrics.checklist_done}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                tamamlandi
              </p>
            </div>
          </div>
        )}

        {/* Buyer-visible Fields */}
        {fields.length > 0 ? (
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Onaylanmis Alanlar ({fields.length})
            </h3>
            <FieldCategoryAccordion
              fields={fields}
            />
          </div>
        ) : (
          <div className="border border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center mt-8">
            <p className="text-gray-500">
              Henuz alici gorunur alan bulunmuyor.
              Alanlar admin tarafindan onaylandiktan sonra burada gorunecektir.
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="mt-8 flex justify-end gap-3">
          {caseId && (
            <button
              onClick={handleDownloadReport}
              disabled={downloading}
              className="px-6 py-3 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {downloading ? "Indiriliyor..." : "Rapor Indir"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
