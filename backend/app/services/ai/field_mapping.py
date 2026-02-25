"""
Canonical field definitions per document type.

Pure-data module — no logic, no imports beyond stdlib.
Used by ClaudeExtractor (prompt building) and frontend (labels/grouping).
"""

# --- Canonical keys expected per doc_type ---
DOC_TYPE_FIELDS: dict[str, list[str]] = {
    "invoice": [
        "shipment.invoice_number",
        "shipment.invoice_date",
        "shipment.total_quantity",
        "shipment.unit",
        "customs.hs_code",
        "product.sku",
        "product.name",
        "factory.country",
    ],
    "packing_list": [
        "shipment.packing_list_number",
        "shipment.total_quantity",
    ],
    "certificate": [
        "certificate.oekotex.number",
        "certificate.oekotex.valid_until",
        "certificate.issuer",
    ],
    "test_report": [
        "test_report.lab_name",
        "test_report.report_number",
        "test_report.report_date",
        "test_report.result_pass_fail",
        "material.composition.cotton_pct",
        "material.composition.elastane_pct",
    ],
    "sds": [
        "sds.exists",
        "chemical.restricted_substances_pass_fail",
    ],
    "bom": [
        "material.composition.cotton_pct",
        "material.composition.elastane_pct",
        "material.composition.total_pct",
        "product.sku",
        "product.name",
        "batch.id",
        "batch.production_date_from",
        "batch.production_date_to",
        "factory.name",
        "factory.country",
    ],
}

# --- UI labels for each canonical key ---
FIELD_LABELS: dict[str, str] = {
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
    "batch.id": "Batch Number",
    "batch.production_date_from": "Production Start",
    "batch.production_date_to": "Production End",
}

# --- Category grouping for UI accordion ---
FIELD_CATEGORIES: dict[str, list[str]] = {
    "Identity": [
        "shipment.invoice_number",
        "shipment.invoice_date",
        "shipment.packing_list_number",
        "product.sku",
        "product.name",
        "batch.id",
    ],
    "Material": [
        "material.composition.cotton_pct",
        "material.composition.elastane_pct",
        "material.composition.total_pct",
        "shipment.total_quantity",
        "shipment.unit",
    ],
    "Certificate": [
        "certificate.oekotex.number",
        "certificate.oekotex.valid_until",
        "certificate.issuer",
    ],
    "Test": [
        "test_report.lab_name",
        "test_report.report_number",
        "test_report.report_date",
        "test_report.result_pass_fail",
    ],
    "SDS": [
        "sds.exists",
        "chemical.restricted_substances_pass_fail",
    ],
    "Factory": [
        "factory.name",
        "factory.country",
    ],
    "Production": [
        "batch.production_date_from",
        "batch.production_date_to",
    ],
    "Customs": [
        "customs.hs_code",
    ],
}
