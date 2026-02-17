"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getRole, clearAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";

interface CaseItem {
  id: string;
  reference_no: string;
  product_group: string;
  status: string;
  date_from: string | null;
  date_to: string | null;
  document_count: number;
  created_at: string;
}

interface CaseCreateResponse {
  case_id: string;
  status: string;
}

export default function SupplierCasesPage() {
  const router = useRouter();
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  // Form state
  const [referenceNo, setReferenceNo] = useState("");
  const [productGroup, setProductGroup] = useState("textiles");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [notes, setNotes] = useState("");

  const fetchCases = useCallback(async () => {
    try {
      const data = await apiFetch<CaseItem[]>("/cases");
      setCases(data);
    } catch {
      // silently handle — empty state is fine
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const role = getRole();
    if (!role || role !== "supplier") {
      router.replace("/login");
      return;
    }
    fetchCases();
  }, [router, fetchCases]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError("");

    try {
      const res = await apiFetch<CaseCreateResponse>("/cases", {
        method: "POST",
        body: JSON.stringify({
          reference_no: referenceNo,
          product_group: productGroup,
          date_from: dateFrom || null,
          date_to: dateTo || null,
          notes: notes || null,
        }),
      });
      router.push(`/supplier/cases/${res.case_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold">Paketlerim</h1>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
            >
              Yeni Paket Olustur
            </button>
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
        </div>

        {/* Create Case Form */}
        {showForm && (
          <div className="mb-8 p-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/50">
            <h2 className="text-lg font-semibold mb-4">Yeni Paket</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Referans No *
                </label>
                <input
                  type="text"
                  value={referenceNo}
                  onChange={(e) => setReferenceNo(e.target.value)}
                  required
                  placeholder="ORN-2026-001"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Urun Grubu
                </label>
                <select
                  value={productGroup}
                  onChange={(e) => setProductGroup(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="textiles">Tekstil</option>
                  <option value="footwear">Ayakkabi</option>
                  <option value="accessories">Aksesuar</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Baslangic Tarihi
                  </label>
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Bitis Tarihi
                  </label>
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notlar
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {error && (
                <div className="p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                  <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={creating || !referenceNo}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {creating ? "Olusturuluyor..." : "Olustur"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  Iptal
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Cases List */}
        {loading ? (
          <p className="text-gray-500 text-center py-12">Yukleniyor...</p>
        ) : cases.length === 0 ? (
          <div className="border border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
            <p className="text-gray-500">
              Henuz paket yok. Yukaridaki butonu kullanarak yeni bir paket olusturun.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {cases.map((c) => (
              <button
                key={c.id}
                onClick={() => router.push(`/supplier/cases/${c.id}`)}
                className="w-full text-left p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 transition-colors bg-white dark:bg-gray-800/50"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {c.reference_no}
                    </p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <span>{c.product_group}</span>
                      <span>{c.document_count} dosya</span>
                      {c.date_from && (
                        <span>
                          {c.date_from}
                          {c.date_to ? ` — ${c.date_to}` : ""}
                        </span>
                      )}
                      <span>
                        {new Date(c.created_at).toLocaleDateString("tr-TR")}
                      </span>
                    </div>
                  </div>
                  <StatusBadge status={c.status} />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
