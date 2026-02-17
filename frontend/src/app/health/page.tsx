"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface HealthData {
  status: string;
  version: string;
  db_connected: boolean;
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<HealthData>("/health")
      .then(setHealth)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 font-[family-name:var(--font-geist-sans)]">
      <h1 className="text-2xl font-bold mb-6">System Health</h1>

      {loading && <p className="text-gray-500">Checking...</p>}

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-red-700 dark:text-red-400">Backend unreachable: {error}</p>
        </div>
      )}

      {health && (
        <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-700 space-y-3 min-w-[300px]">
          <div className="flex justify-between">
            <span className="text-gray-500">Status</span>
            <span className="font-medium">{health.status}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Version</span>
            <span className="font-mono text-sm">{health.version}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Database</span>
            <span
              className={
                health.db_connected
                  ? "text-green-600 dark:text-green-400"
                  : "text-red-600 dark:text-red-400"
              }
            >
              {health.db_connected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
