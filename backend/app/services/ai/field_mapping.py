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

# --- Turkish UI labels for each canonical key ---
FIELD_LABELS: dict[str, str] = {
    "shipment.invoice_number": "Fatura Numarasi",
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
    "material.composition.cotton_pct": "Pamuk Orani (%)",
    "material.composition.elastane_pct": "Elastan Orani (%)",
    "material.composition.total_pct": "Toplam Oran (%)",
    "sds.exists": "SDS Mevcut",
    "chemical.restricted_substances_pass_fail": "Kisitli Madde Sonucu",
    "batch.id": "Parti Numarasi",
    "batch.production_date_from": "Uretim Baslangic",
    "batch.production_date_to": "Uretim Bitis",
}

# --- Category grouping for UI accordion ---
FIELD_CATEGORIES: dict[str, list[str]] = {
    "Kimlik": [
        "shipment.invoice_number",
        "shipment.invoice_date",
        "shipment.packing_list_number",
        "product.sku",
        "product.name",
        "batch.id",
    ],
    "Malzeme": [
        "material.composition.cotton_pct",
        "material.composition.elastane_pct",
        "material.composition.total_pct",
        "shipment.total_quantity",
        "shipment.unit",
    ],
    "Sertifika": [
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
    "Fabrika": [
        "factory.name",
        "factory.country",
    ],
    "Uretim": [
        "batch.production_date_from",
        "batch.production_date_to",
    ],
    "Gumruk": [
        "customs.hs_code",
    ],
}
