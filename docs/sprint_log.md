# Sprint Log

## Sprint 0 — Skeleton + Infra Setup

**Goal**: Bootstrap monorepo with runnable backend and frontend, database schema, and project documentation.

**Delivered**:
- Backend: FastAPI app at `/v1` prefix with health, auth, and invite endpoints
- Auth: JWT-based login (PyJWT + bcrypt), RBAC middleware (get_current_user, require_role)
- 3 roles: supplier, buyer, admin
- Invite flow: buyer/admin creates invite → supplier accepts → Tenant + User + BuyerSupplierLink created
- Endpoints: POST /v1/auth/login, POST /v1/auth/accept-invite, GET /v1/auth/me, POST /v1/invites, GET /v1/invites
- 7 SQLAlchemy models: Tenant, User, Invite, Case, Document, ExtractedField, BuyerSupplierLink
- Frontend: Next.js 14 (App Router) with login page, role-based dashboards (/supplier/cases, /buyer/dashboard, /admin/review-queue)
- Seed script: `backend/scripts/seed_dev.py` creates buyer tenant, buyer user, admin user, pending invite
- Infra: Docker Compose (Postgres + backend + frontend), Dockerfiles
- Docs: README, architecture overview, data governance, this sprint log

**Key decisions**:
- Sync SQLAlchemy for MVP simplicity (async migration possible later)
- String-based roles (not DB enums) to avoid migration friction
- UUID primary keys for multi-tenant safety
- ExtractedField.page and .snippet are NOT NULL — enforces evidence linkage at DB level
- DPPSnapshot model removed from Sprint 0 scope (will be added when needed)
- BuyerSupplierLink model bridges buyer and supplier tenants via invite
- API prefix `/v1` (not `/api`) for versioned API design
- JWT auth in app middleware (not Supabase RLS) for MVP simplicity
