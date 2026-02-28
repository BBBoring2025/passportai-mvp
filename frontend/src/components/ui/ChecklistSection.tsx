"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

export interface ChecklistItem {
  id: string;
  case_id: string;
  type: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  related_field_id: string | null;
  completed_at: string | null;
  created_at: string;
}

interface ChecklistSectionProps {
  items: ChecklistItem[];
  onItemUpdate: () => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  high: "border-l-red-500",
  medium: "border-l-yellow-500",
  low: "border-l-blue-500",
};

const SEVERITY_LABELS: Record<string, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

const TYPE_LABELS: Record<string, string> = {
  missing_field: "Missing Field",
  missing_document: "Missing Document",
  conflict_detected: "Conflicting Value",
  expired_document: "Expired Document",
  composition_error: "Composition Error",
};

export default function ChecklistSection({
  items,
  onItemUpdate,
}: ChecklistSectionProps) {
  const [updating, setUpdating] = useState<string | null>(null);

  const handleMarkDone = async (itemId: string) => {
    setUpdating(itemId);
    try {
      await apiFetch(`/checklist/${itemId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: "done" }),
      });
      onItemUpdate();
    } catch (err) {
      console.error("Failed to update checklist item:", err);
    } finally {
      setUpdating(null);
    }
  };

  const openItems = items.filter((i) => i.status !== "done");
  const doneItems = items.filter((i) => i.status === "done");

  if (items.length === 0) {
    return (
      <div className="border border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
        <p className="text-gray-500 text-sm">
          No checklist created yet. Run validation.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {openItems.map((item) => (
        <div
          key={item.id}
          className={`border-l-4 ${
            SEVERITY_COLORS[item.severity] ||
            "border-l-gray-300"
          } bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-r-lg p-4 flex items-start justify-between gap-4`}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                {TYPE_LABELS[item.type] || item.type}
              </span>
              <span className="text-xs text-gray-400">
                {SEVERITY_LABELS[item.severity] ||
                  item.severity}
              </span>
            </div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {item.title}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {item.description}
            </p>
          </div>
          <button
            onClick={() => handleMarkDone(item.id)}
            disabled={updating === item.id}
            className="px-3 py-1.5 text-xs font-medium rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {updating === item.id
              ? "..."
              : "Resolve"}
          </button>
        </div>
      ))}

      {doneItems.length > 0 && (
        <details className="mt-4">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
            Completed ({doneItems.length})
          </summary>
          <div className="mt-2 space-y-1">
            {doneItems.map((item) => (
              <div
                key={item.id}
                className="bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 rounded-lg p-3 opacity-60"
              >
                <p className="text-xs text-gray-500 line-through">
                  {item.title}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
