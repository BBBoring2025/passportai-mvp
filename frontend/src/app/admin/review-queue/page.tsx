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
  "shipment.invoice_number": "Invoice No",
  "shipment.invoice_date": "Invoice Date",
  "shipment.total_quantity": "Total Quantity",
  "shipment.unit": "Unit",
  "customs.hs_code": "HS Code",
  "product.sku": "Product Code (SKU)",
  "product.name": "Product Name",
  "factory.country": "Factory Country",
  "factory.name": "Factory Name",
  "shipment.packing_list_number": "Packing List No",
  "certificate.oekotex.number": "OEKO-TEX Certificate No",
  "certificate.oekotex.valid_until": "Validity Date",
  "certificate.issuer": "Issuing Body",
  "test_report.lab_name": "Laboratory Name",
  "test_report.report_number": "Report Number",
  "test_report.report_date": "Report Date",
  "test_report.result_pass_fail": "Result (Pass/Fail)",
  "material.composition.cotton_pct": "Cotton Ratio (%)",
  "material.composition.elastane_pct": "Elastane Ratio (%)",
  "material.composition.total_pct": "Total Composition (%)",
  "sds.exists": "SDS Available",
  "chemical.restricted_substances_pass_fail": "Restricted Substance Result",
  "batch.id": "Lot Number",
  "batch.production_date_from": "Production Start",
  "batch.production_date_to": "Production End",
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
        err instanceof Error ? err.message : "Queue could not be loaded"
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
        err instanceof Error ? err.message : "Approval failed"
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
        err instanceof Error ? err.message : "Rejection failed"
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
            Loading...
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
            <h1 className="text-2xl font-bold">L2 Approval Queue</h1>
            <p className="text-sm text-gray-500 mt-1">
              {fields.length} field(s) pending review
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
              No fields pending review.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Field
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Value
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Source Text
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Supplier
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Package
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400 text-right">
                    Action
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
                            placeholder="Reason (optional)"
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
                              : "Reject"}
                          </button>
                          <button
                            onClick={() => {
                              setRejectingId(null);
                              setRejectReason("");
                            }}
                            className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
                          >
                            Cancel
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
                              : "Approve"}
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
                            Reject
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
