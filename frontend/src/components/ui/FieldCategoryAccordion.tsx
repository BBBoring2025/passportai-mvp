"use client";

import { useState } from "react";
import StatusBadge from "./StatusBadge";

// English labels for canonical keys
const FIELD_LABELS: Record<string, string> = {
  "shipment.invoice_number": "Invoice Number",
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

// Category grouping
const FIELD_CATEGORIES: Record<string, string[]> = {
  Identity: [
    "shipment.invoice_number",
    "shipment.invoice_date",
    "shipment.packing_list_number",
    "product.sku",
    "product.name",
    "batch.id",
  ],
  Material: [
    "material.composition.cotton_pct",
    "material.composition.elastane_pct",
    "material.composition.total_pct",
    "shipment.total_quantity",
    "shipment.unit",
  ],
  Certificate: [
    "certificate.oekotex.number",
    "certificate.oekotex.valid_until",
    "certificate.issuer",
  ],
  Test: [
    "test_report.lab_name",
    "test_report.report_number",
    "test_report.report_date",
    "test_report.result_pass_fail",
  ],
  SDS: [
    "sds.exists",
    "chemical.restricted_substances_pass_fail",
  ],
  Factory: ["factory.name", "factory.country"],
  Production: ["batch.production_date_from", "batch.production_date_to"],
  Customs: ["customs.hs_code"],
};

export interface ExtractedField {
  id: string;
  document_id: string;
  case_id: string;
  canonical_key: string;
  value: string;
  unit: string | null;
  page: number;
  snippet: string;
  confidence: number | null;
  tier: string;
  status: string;
  visibility: string;
  created_from: string;
  created_at: string;
  document_filename: string | null;
  doc_type: string | null;
}

interface FieldCategoryAccordionProps {
  fields: ExtractedField[];
  onViewEvidence?: (
    documentId: string,
    page: number,
    snippet: string
  ) => void;
}

export default function FieldCategoryAccordion({
  fields,
  onViewEvidence,
}: FieldCategoryAccordionProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Build a lookup: canonical_key → field
  const fieldMap: Record<string, ExtractedField> = {};
  for (const f of fields) {
    // If duplicate keys, keep highest confidence
    const existing = fieldMap[f.canonical_key];
    if (
      !existing ||
      (f.confidence ?? 0) > (existing.confidence ?? 0)
    ) {
      fieldMap[f.canonical_key] = f;
    }
  }

  const toggleCategory = (cat: string) => {
    setExpanded((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  // Only show categories that have at least one field
  const visibleCategories = Object.entries(FIELD_CATEGORIES).filter(
    ([, keys]) => keys.some((k) => fieldMap[k])
  );

  if (visibleCategories.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {visibleCategories.map(([category, keys]) => {
        const categoryFields = keys
          .map((k) => ({ key: k, field: fieldMap[k] }))
          .filter((x) => x.field);
        const isOpen = expanded[category] ?? true; // default open

        return (
          <div
            key={category}
            className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
          >
            {/* Category header */}
            <button
              onClick={() => toggleCategory(category)}
              className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
            >
              <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                {category}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  {categoryFields.length} fields
                </span>
                <span className="text-gray-400 text-xs">
                  {isOpen ? "▲" : "▼"}
                </span>
              </div>
            </button>

            {/* Fields */}
            {isOpen && (
              <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {categoryFields.map(({ key, field }) => (
                  <div
                    key={key}
                    className="px-4 py-3 flex items-center gap-4"
                  >
                    {/* Label */}
                    <div className="w-44 flex-shrink-0">
                      <p className="text-xs text-gray-500">
                        {FIELD_LABELS[key] || key}
                      </p>
                    </div>

                    {/* Value */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {field.value}
                        {field.unit && (
                          <span className="text-gray-500 ml-1">
                            {field.unit}
                          </span>
                        )}
                      </p>
                      {field.document_filename && (
                        <p className="text-xs text-gray-400 truncate">
                          {field.document_filename}
                        </p>
                      )}
                    </div>

                    {/* Confidence */}
                    {field.confidence != null && (
                      <span className="text-xs text-gray-400 tabular-nums">
                        {Math.round(field.confidence * 100)}%
                      </span>
                    )}

                    {/* Tier badge */}
                    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                      {field.tier}
                    </span>

                    {/* Status badge */}
                    <StatusBadge status={field.status} />

                    {/* Evidence link */}
                    {onViewEvidence && (
                      <button
                        onClick={() =>
                          onViewEvidence(
                            field.document_id,
                            field.page,
                            field.snippet
                          )
                        }
                        className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline whitespace-nowrap"
                      >
                        View Evidence
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
