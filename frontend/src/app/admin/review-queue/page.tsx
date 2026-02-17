"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getRole, clearAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";

interface AdminField {
  id: string;
  document_id: string;
  canonical_key: string;
  value: string;
  snippet: string | null;
  page_number: number | null;
  confidence: number | null;
  tier: string;
  status: string;
  visibility: string;
  supplier_name: string;
  case_reference_no: string;
  created_at: string;
}

// Canonical keys matching backend/app/services/ai/field_mapping.py
const FIELD_LABELS: Record<string, string> = {
  "shipment.invoice_number": "Fatura No",
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
  "material.composition.cotton_pct": "Pamuk %",
  "material.composition.elastane_pct": "Elastan %",
  "material.composition.total_pct": "Toplam %",
  "sds.exists": "SDS Mevcut",
  "chemical.restricted_substances_pass_fail": "Kisitli Madde Sonucu",
  "batch.id": "Parti Numarasi",
  "batch.production_date_from": "Uretim Baslangic",
  "batch.production_date_to": "Uretim Bitis",
};

export default function AdminReviewQueuePage() {
  const router = useRouter();
  const [fields, setFields] = useState<AdminField[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  useEffect(() => {
    const role = getRole();
    if (!role || role !== "admin") {
      router.replace("/login");
    }
  }, [router]);

  const fetchQueue = useCallback(async () => {
    try {
      const data = await apiFetch<AdminField[]>(
        "/admin/review-queue?status=pending_review"
      );
      setFields(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Kuyruk yuklenemedi"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const handleApprove = async (fieldId: string) => {
    setActionInProgress(fieldId);
    setError("");
    try {
      await apiFetch(`/admin/fields/${fieldId}/approve`, {
        method: "POST",
      });
      // Remove from list
      setFields((prev) => prev.filter((f) => f.id !== fieldId));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Onaylama basarisiz"
      );
    } finally {
      setActionInProgress(null);
    }
  };

  const handleRejectSubmit = async (fieldId: string) => {
    setActionInProgress(fieldId);
    setError("");
    try {
      await apiFetch(`/admin/fields/${fieldId}/reject`, {
        method: "POST",
        body: JSON.stringify({
          reason: rejectReason || undefined,
        }),
      });
      setFields((prev) => prev.filter((f) => f.id !== fieldId));
      setRejectingId(null);
      setRejectReason("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Reddetme basarisiz"
      );
    } finally {
      setActionInProgress(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
        <div className="max-w-6xl mx-auto">
          <p className="text-gray-500 text-center py-12">
            Yukleniyor...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold">L2 Onay Kuyrugu</h1>
            <p className="text-sm text-gray-500 mt-1">
              {fields.length} alan inceleme bekliyor
            </p>
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

        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-700 dark:text-red-400">
              {error}
            </p>
          </div>
        )}

        {fields.length === 0 ? (
          <div className="border border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
            <p className="text-gray-500">
              Inceleme bekleyen alan bulunmuyor.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Alan
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Deger
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Kaynak Metin
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Tedarikci
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Paket
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Durum
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400 text-right">
                    Islem
                  </th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field) => (
                  <tr
                    key={field.id}
                    className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                  >
                    <td className="py-3 px-4">
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {FIELD_LABELS[field.canonical_key] ||
                          field.canonical_key}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300 max-w-[200px] truncate">
                      {field.value}
                    </td>
                    <td className="py-3 px-4 text-gray-500 max-w-[200px] truncate text-xs italic">
                      {field.snippet
                        ? field.snippet.length > 80
                          ? field.snippet.slice(0, 80) + "..."
                          : field.snippet
                        : "—"}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                      {field.supplier_name}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
                      {field.case_reference_no}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={field.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      {rejectingId === field.id ? (
                        <div className="flex items-center gap-2 justify-end">
                          <input
                            type="text"
                            placeholder="Sebep (opsiyonel)"
                            value={rejectReason}
                            onChange={(e) =>
                              setRejectReason(e.target.value)
                            }
                            className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 w-36"
                          />
                          <button
                            onClick={() =>
                              handleRejectSubmit(field.id)
                            }
                            disabled={
                              actionInProgress === field.id
                            }
                            className="px-2 py-1 text-xs font-medium rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-40"
                          >
                            {actionInProgress === field.id
                              ? "..."
                              : "Reddet"}
                          </button>
                          <button
                            onClick={() => {
                              setRejectingId(null);
                              setRejectReason("");
                            }}
                            className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
                          >
                            Iptal
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 justify-end">
                          <button
                            onClick={() =>
                              handleApprove(field.id)
                            }
                            disabled={
                              actionInProgress === field.id
                            }
                            className="px-3 py-1.5 text-xs font-medium rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            {actionInProgress === field.id
                              ? "..."
                              : "Onayla"}
                          </button>
                          <button
                            onClick={() =>
                              setRejectingId(field.id)
                            }
                            disabled={
                              actionInProgress === field.id
                            }
                            className="px-3 py-1.5 text-xs font-medium rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            Reddet
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
