# PassportAI Architecture

## Data Flow

```
Data Intake → Evidence Vault → Rules Engine → DPP Output
```

1. **Data Intake**: Supplier uploads PDF/JPG/PNG documents to a Case
2. **Evidence Vault**: Documents stored in Supabase Storage, classified by type (heuristic first, LLM fallback)
3. **Rules Engine**: AI extracts structured fields with mandatory evidence linkage (page + snippet). Fields validated against canonical schema.
4. **DPP Output**: Extracted fields assembled into immutable DPP snapshots. L1 = self-declared readiness, L2 = document-supported with human approval.

## Core Invariant: Invite-Led Flow

```
Buyer creates Invite → Supplier receives link → Supplier signs up → Supplier creates Case → Backend resolves buyer from invite
```

The supplier never knows the `buyer_tenant_id`. The Invite is the sole bridge.

## API Route Plan

All endpoints use the `/v1` prefix.

### Sprint 0 (current)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | Health check with DB connectivity |
| POST | `/v1/auth/login` | Email + password login, returns JWT |
| POST | `/v1/auth/accept-invite` | Supplier accepts invite, creates tenant + user |
| GET | `/v1/auth/me` | Current user profile with tenant info |
| POST | `/v1/invites` | Buyer/admin creates supplier invite |
| GET | `/v1/invites` | List tenant's invites |

### Sprint 1 — Cases & Documents
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/cases` | Create case (from invite) |
| GET | `/v1/cases` | List cases |
| GET | `/v1/cases/{id}` | Case detail |
| PATCH | `/v1/cases/{id}` | Update case |
| POST | `/v1/cases/{id}/documents` | Upload document |
| GET | `/v1/cases/{id}/documents` | List documents |
| GET | `/v1/documents/{id}` | Document detail |

### Sprint 2 — AI Extraction
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/documents/{id}/extract` | Trigger AI extraction |
| GET | `/v1/documents/{id}/fields` | List extracted fields |

### Sprint 3 — DPP Snapshots
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/cases/{id}/dpp` | Generate DPP snapshot |
| GET | `/v1/cases/{id}/dpp` | List snapshots |
| GET | `/v1/cases/{id}/dpp/{version}` | Snapshot detail |
| PATCH | `/v1/cases/{id}/dpp/{version}` | Submit/approve/reject |

## Database Schema

See `backend/app/models/` for SQLAlchemy definitions.

```
Tenant (1) ----< (N) User
Tenant (1) ----< (N) Invite              [buyer_tenant_id]
Tenant (1) ----< (N) Case                [supplier_tenant_id]
Tenant (1) ----< (N) BuyerSupplierLink   [buyer_tenant_id / supplier_tenant_id]
Invite (1) ----< (N) Case                [invite_id]
Invite (1) ----< (1) BuyerSupplierLink   [invite_id]
Case   (1) ----< (N) Document
Document (1) --< (N) ExtractedField
```
