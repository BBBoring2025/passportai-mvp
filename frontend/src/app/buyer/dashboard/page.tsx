"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getRole, clearAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";

interface SupplierMetric {
  tenant_name: string;
  tenant_id: string;
  latest_case_id: string | null;
  coverage_pct: number;
  conflict_rate: number;
  days_to_ready: number | null;
  l1_count: number;
  l2_count: number;
  field_count: number;
  status: string;
}

interface BuyerDashboardData {
  suppliers: SupplierMetric[];
  aggregate: {
    total_suppliers: number;
    avg_coverage: number;
    total_conflicts: number;
    avg_days_to_ready: number | null;
  };
}

function coverageColor(pct: number): string {
  if (pct >= 80) return "text-green-600 dark:text-green-400";
  if (pct >= 50) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
}

export default function BuyerDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<BuyerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Invite form state
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteMessage, setInviteMessage] = useState("");
  const [inviteLink, setInviteLink] = useState("");

  useEffect(() => {
    const role = getRole();
    if (!role || (role !== "buyer" && role !== "admin")) {
      router.replace("/login");
    }
  }, [router]);

  const fetchDashboard = useCallback(async () => {
    try {
      const d = await apiFetch<BuyerDashboardData>("/dashboard/buyer");
      setData(d);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Dashboard could not be loaded"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    setInviting(true);
    setInviteMessage("");
    setInviteLink("");
    try {
      const invite = await apiFetch<{ token: string }>("/invites", {
        method: "POST",
        body: JSON.stringify({ supplier_email: inviteEmail }),
      });
      const link = `${window.location.origin}/accept-invite?token=${invite.token}`;
      setInviteLink(link);
      setInviteMessage(`Invite sent: ${inviteEmail}`);
      setInviteEmail("");
      setShowInviteForm(false);
    } catch (err) {
      setInviteMessage(
        err instanceof Error ? err.message : "Invite could not be sent"
      );
    } finally {
      setInviting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
        <div className="max-w-6xl mx-auto">
          <p className="text-gray-500 text-center py-12">Loading...</p>
        </div>
      </div>
    );
  }

  const agg = data?.aggregate;
  const suppliers = data?.suppliers || [];

  return (
    <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold">Supplier Readiness Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">
              DPP readiness status of connected suppliers
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/buyer/settings")}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Settings
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

        {/* Aggregate Metrics Cards */}
        {agg && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Total Suppliers
              </p>
              <p className="text-2xl font-bold mt-1">{agg.total_suppliers}</p>
            </div>
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Average Coverage
              </p>
              <p className={`text-2xl font-bold mt-1 ${coverageColor(agg.avg_coverage)}`}>
                {agg.avg_coverage.toFixed(1)}%
              </p>
            </div>
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Total Conflicts
              </p>
              <p className="text-2xl font-bold mt-1">{agg.total_conflicts}</p>
            </div>
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Avg. Readiness Time
              </p>
              <p className="text-2xl font-bold mt-1">
                {agg.avg_days_to_ready != null
                  ? `${agg.avg_days_to_ready.toFixed(1)} days`
                  : "—"}
              </p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Invite message + link */}
        {inviteMessage && (
          <div className="mb-4 p-3 rounded bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-700 dark:text-blue-400">
              {inviteMessage}
            </p>
            {inviteLink && (
              <div className="mt-2 flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={inviteLink}
                  className="flex-1 px-2 py-1 text-xs rounded border border-blue-300 dark:border-blue-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono"
                />
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(inviteLink);
                  }}
                  className="px-3 py-1 text-xs font-medium rounded bg-blue-600 text-white hover:bg-blue-700 whitespace-nowrap"
                >
                  Copy
                </button>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 mb-4">
          <button
            onClick={() => setShowInviteForm(!showInviteForm)}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Invite Supplier
          </button>
        </div>

        {/* Invite Form */}
        {showInviteForm && (
          <form
            onSubmit={handleInvite}
            className="mb-6 p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex items-end gap-3"
          >
            <div className="flex-1">
              <label className="text-xs font-medium text-gray-500 block mb-1">
                Supplier Email
              </label>
              <input
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="supplier@example.com"
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={inviting || !inviteEmail}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {inviting ? "Sending..." : "Send Invite"}
            </button>
            <button
              type="button"
              onClick={() => setShowInviteForm(false)}
              className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700"
            >
              Cancel
            </button>
          </form>
        )}

        {/* Supplier Table */}
        {suppliers.length === 0 ? (
          <div className="border border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
            <p className="text-gray-500">
              No connected suppliers. Start by inviting a supplier.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Supplier Name
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Coverage %
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Conflicts
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    L1 / L2
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Readiness
                  </th>
                  <th className="py-3 px-4 font-medium text-gray-500 dark:text-gray-400 text-right">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((s) => (
                  <tr
                    key={s.tenant_id}
                    className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                  >
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      {s.tenant_name}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className={`py-3 px-4 font-bold ${coverageColor(s.coverage_pct)}`}>
                      {s.coverage_pct.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                      {s.conflict_rate > 0
                        ? `${s.conflict_rate.toFixed(1)}%`
                        : "—"}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
                      {s.l1_count} / {s.l2_count}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                      {s.days_to_ready != null
                        ? `${s.days_to_ready.toFixed(1)} days`
                        : "—"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {s.latest_case_id ? (
                        <button
                          onClick={() =>
                            router.push(
                              `/buyer/suppliers/${s.tenant_id}?case=${s.latest_case_id}`
                            )
                          }
                          className="px-3 py-1.5 text-xs font-medium rounded bg-blue-600 text-white hover:bg-blue-700"
                        >
                          Details
                        </button>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
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
