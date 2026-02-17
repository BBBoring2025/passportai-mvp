# PassportAI — DPP Operations Module

Digital Product Passport (DPP) operations platform for textile supply chains. Enables buyers to invite suppliers, who upload trade documents (invoices, certificates, test reports, etc.). AI extracts structured fields with evidence linkage, building toward auditable DPP snapshots.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL (Supabase) |
| Storage | Supabase Storage (S3-compatible) |
| AI | Claude Sonnet 4.5 via Anthropic API |
| OCR | PyMuPDF + Tesseract |
| Auth | Supabase Auth + JWT, RBAC in FastAPI |
| Deploy | Vercel (frontend), Railway (backend), Supabase (DB) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (local or Supabase)

### Backend

```bash
cd backend
cp .env.example .env        # edit with your DB credentials
pip install -e ".[dev]"
alembic upgrade head         # run migrations
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000. API docs at http://localhost:8000/docs.

### Frontend

```bash
cd frontend
cp .env.example .env.local   # edit API URL if needed
npm install
npm run dev
```

Frontend runs at http://localhost:3000.

### Docker Compose (alternative)

```bash
docker-compose up --build
```

Starts PostgreSQL, backend, and frontend together.

## Project Structure

```
passportai/
├── backend/          # FastAPI + SQLAlchemy
├── frontend/         # Next.js 14 + Tailwind
├── docs/             # Architecture, data governance
├── sample_docs/      # Test PDFs + ground truth CSV
└── docker-compose.yml
```

## Architecture

**Data Intake** → **Evidence Vault** → **Rules Engine** → **DPP Output**

- Buyer invites Supplier (invite-led flow)
- Supplier uploads documents to a Case
- AI extracts fields with mandatory evidence (page + snippet)
- DPP snapshot assembled from extracted fields
- L1 = self-declared readiness, L2 = document-supported (human approval)
