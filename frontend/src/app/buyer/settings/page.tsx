"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getRole, clearAuth } from "@/lib/auth";

export default function BuyerSettingsPage() {
  const router = useRouter();
  const [minTier, setMinTier] = useState("L1");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const role = getRole();
    if (!role || (role !== "buyer" && role !== "admin")) {
      router.replace("/login");
      return;
    }
    // Load saved preference
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("buyer_min_tier");
      if (stored === "L1" || stored === "L2") {
        setMinTier(stored);
      }
    }
  }, [router]);

  const handleSave = () => {
    localStorage.setItem("buyer_min_tier", minTier);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <button
              onClick={() => router.push("/buyer/dashboard")}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2 flex items-center gap-1"
            >
              &larr; Dashboard
            </button>
            <h1 className="text-2xl font-bold">Settings</h1>
            <p className="text-sm text-gray-500 mt-1">
              Configure buyer preferences
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

        {/* Tier preference */}
        <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            Minimum Acceptance Tier
          </h2>
          <p className="text-xs text-gray-500 mb-4">
            Select the minimum validation tier required for field data
            acceptance.
          </p>

          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="minTier"
                value="L1"
                checked={minTier === "L1"}
                onChange={() => setMinTier("L1")}
                className="w-4 h-4 text-blue-600"
              />
              <div>
                <span className="text-sm font-medium">L1 — Automatic Extraction</span>
                <p className="text-xs text-gray-500">
                  AI-extracted fields are accepted (faster, lower accuracy)
                </p>
              </div>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="minTier"
                value="L2"
                checked={minTier === "L2"}
                onChange={() => setMinTier("L2")}
                className="w-4 h-4 text-blue-600"
              />
              <div>
                <span className="text-sm font-medium">
                  L2 — Admin Approved (Recommended)
                </span>
                <p className="text-xs text-gray-500">
                  Only fields reviewed and approved by admin are accepted
                  (slower, higher accuracy)
                </p>
              </div>
            </label>
          </div>

          <div className="mt-6 flex items-center gap-3">
            <button
              onClick={handleSave}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            >
              Save
            </button>
            {saved && (
              <span className="text-sm text-green-600 dark:text-green-400">
                Saved!
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
