# PassportAI MVP - Claude Code Baslangic Rehberi

## Adim 1: Masaustunde Klasor Olustur

Masaustunde (veya istedigin yerde) bir klasor ac:
```
passportai/
```

Icine su dosyalari koy:
- `PassportAI_MVP_Sprint_Guide.docx` (Sprint rehberi - az once indirdigin)
- `sample_docs/` klasoru (6 PDF + 1 CSV - az once indirdigin)

## Adim 2: Claude Code'u Ac

Terminal / komut satirini ac ve su klasore git:
```bash
cd ~/Desktop/passportai
```

Claude Code'u baslat:
```bash
claude
```

(Eger Claude Code kurulu degilse: `npm install -g @anthropic-ai/claude-code`)

## Adim 3: Ilk Prompt'u Yapistir

Claude Code acildiginda, asagidaki metni AYNEN kopyala-yapistir:

---

```
You are implementing SalesShield / PassportAI MVP.

PRODUCT IDENTITY:
- DPP Operations Module (NOT a passport generator)
- Architecture: Data Intake > Evidence Vault > Rules Engine > DPP Output
- AI is strictly extraction & mapping from documents
- AI must NOT generate compliance claims, carbon footprint, or regulatory predictions
- Every extracted field MUST be source-linked to evidence (minimum: page + snippet)
- If there is no evidence snippet, do NOT create the value
- L1 = readiness (self-declared), NOT compliance
- L2 = document-supported, requires human approval before buyer visibility
- Buyer must NOT download supplier raw documents (data minimization)

STACK (do NOT change):
- Frontend: Next.js 14 (App Router) with TypeScript + Tailwind CSS
- Backend: Python 3.12 + FastAPI + SQLAlchemy + Pydantic
- Database: PostgreSQL (via Supabase)
- File Storage: Supabase Storage (S3-compatible)
- AI Model: Claude Sonnet 4.5 via Anthropic API (model-agnostic interface)
- OCR: PyMuPDF (text PDFs) + Tesseract (scanned/image fallback)
- Auth: Supabase Auth + JWT. RBAC enforced in FastAPI middleware (NOT Supabase RLS).
  RLS is future; MVP auth is 100% in FastAPI. Supabase = hosted Postgres + Storage only.
- Deploy: Vercel (frontend) + Railway (backend) + Supabase (DB/storage)

CRITICAL ARCHITECTURE RULES:
- Invite flow is CORE (importer-led model). Buyer invites supplier.
  Supplier never needs to know buyer_tenant_id; the invite link creates the relationship.
- Supplier creates Case without specifying buyer; backend resolves buyer from invite link.
- XLSX is NOT supported in MVP. Only PDF/JPG/PNG.
- LLM calls: prefer page-based extraction (not full doc). Use heuristic classification first,
  fall back to LLM only if uncertain. Minimize token usage.
- System-generated values (e.g. batch.id auto-gen) must be marked created_from=system.
- Evidence viewer: 'go to page + show snippet in side panel' is sufficient.
  BBox highlight is optional; do NOT block on it.

DATA GOVERNANCE NOTE (for docs/data_governance.md):
- Documents are processed via Anthropic API for field extraction.
- Minimize personal data sent to LLM (strip pricing, personal names where possible).
- Anthropic API inputs/outputs are deleted within a limited timeframe by default (e.g. 30 days); enterprise zero-retention available by agreement.
- Future: on-prem/private deployment option for enterprise buyers.

SAMPLE DOCUMENTS: There are 6 sample PDF documents in ./sample_docs/ directory:
- 01_commercial_invoice.pdf (Turkish textile exporter invoice)
- 02_packing_list.pdf (Packing list)
- 03_oekotex_certificate.pdf (OEKO-TEX Standard 100 certificate)
- 04_test_report_sgs.pdf (SGS lab test report)
- 05_sds_reactive_dye.pdf (Safety Data Sheet for reactive dye)
- 06_bom_material_declaration.pdf (Bill of Materials / composition declaration)
- golden_set_ground_truth.csv (Ground truth for evaluation harness)
These are for development and testing. Use them in Sprint 3+ for extraction testing.

RULES:
- Minimal complexity. No over-engineering.
- Each sprint must end with: runnable app, updated /docs, short demo script.
- Run tests and lint at end of each sprint.
- Keep AI extraction model-agnostic (interface + implementation separated).

First: inspect the repository and summarize what exists.
Then propose the folder structure and confirm before proceeding.
After confirmation, proceed to Sprint 0.
```

---

## Adim 4: Claude Code Calistiginda Ne Olacak?

Claude Code:
1. Klasoru tarayacak
2. Repo yapisini onerecek
3. Senin onayindan sonra Sprint 0'a baslayacak (auth + RBAC + docs)

Sprint 0 bitince sana "demo checklist" verecek. Kontrol et, calisiyorsa Sprint 1'e gec.

## Adim 5: Sonraki Sprintler

Her sprint bittiginde, Sprint Guide dokumandaki siradaki sprint prompt'unu kopyala-yapistir.
Sira: Sprint 0 > 1 > 2 > 3 > 4 > 5

## Onemli Notlar

- Her sprint sonunda "calisiyor mu?" kontrol et
- Sprint 3'te sample_docs/ klasorunundeki PDF'leri kullanacak (extraction testi)
- Sorun cikarsa Claude Code'a hatayi yapistir, o duzeltecek
- Supabase hesabi lazim (ucretsiz): https://supabase.com
- Vercel hesabi lazim (ucretsiz): https://vercel.com
