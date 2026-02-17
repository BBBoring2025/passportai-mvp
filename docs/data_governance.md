# Data Governance

## Document Processing via Anthropic API

- Documents are processed via the Anthropic API (Claude) for field extraction.
- Only relevant text content is sent to the API — pricing data and personal names are stripped where possible before submission.
- Extraction is page-based (not full-document) to minimize token usage and data exposure.

## Data Retention

- Anthropic API inputs/outputs are deleted within 30 days by default.
- Enterprise zero-retention agreements are available for production deployments.
- Raw documents are stored in Supabase Storage under tenant-scoped paths.

## Data Minimization

- Buyer users cannot download supplier raw documents (data minimization principle).
- Buyers see only the structured DPP snapshot, not the source files.
- Extracted fields include evidence snippets (short text excerpts) rather than full document content.

## Access Control

- RBAC enforced in FastAPI middleware (not database-level RLS in MVP).
- Roles: `buyer_admin`, `buyer_viewer`, `supplier_admin`, `supplier_user`.
- Tenant isolation enforced at the API layer — queries always scoped to the authenticated user's tenant.

## Future Considerations

- On-premises / private deployment option for enterprise buyers requiring full data sovereignty.
- Supabase RLS as a defense-in-depth layer (post-MVP).
- Audit logging for all document access and extraction events.
