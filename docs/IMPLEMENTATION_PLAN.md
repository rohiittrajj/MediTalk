# Implementation plan

This is planned work, not a claim of completion.

## Phase 0 — Repository foundation
- [x] Starter structure and agent instructions.
- [x] Product, architecture, design, security, testing, and status documentation.
- [ ] Verify setup on developer machine.
- [ ] Import verified OneService palette tokens when source assets are available.

## Phase 1 — Application foundation
- [ ] Design tokens, reusable accessible components, typed API client.
- [ ] Database session, SQLAlchemy models, Alembic migrations.
- [ ] Authentication and server-side authorization.
- [ ] CI, lint, type checking, tests, and build.

## Phase 2 — Case and consent
- [ ] Patient case lifecycle and consent history.
- [ ] English/Hindi onboarding and intake session persistence/recovery.

## Phase 3 — Conversational history
- [ ] General history model and adaptive questionnaire rules.
- [ ] Speech adapter and touch/text fallback.
- [ ] Versioned red-flag rules, tests, escalation and fallback instructions.

## Phase 4 — Documents
- [ ] Secure upload and private storage.
- [ ] OCR/extraction adapter, job states, confidence and source references.
- [ ] Timeline and conflict review.

## Phase 5 — Summary and clinician workspace
- [ ] Provenance-aware draft summary.
- [ ] Missing/contradictory data indicators.
- [ ] Clinician queue, edit, accept/reject, audit events, patient recap.

## Phase 6 — AYUSH
- [ ] Configurable assessment mode and relevant traditional assessment fields.
- [ ] Practitioner review; never fabricate missing values.

## Phase 7 — Integrations
- [ ] Select approved speech/OCR/language providers.
- [ ] Authorized identity and FHIR/HIS/EMR adapters where available.
- [ ] Test failure, retry, idempotency, and audit behavior.

## Phase 8 — Hardening and release
- [ ] End-to-end tests for the complete patient-to-clinician journey.
- [ ] Security, privacy, accessibility, upload abuse, and dependency review.
- [ ] Backup/restore, retention/deletion, monitoring, deployment, and incident runbook.

Finish vertical slices end-to-end. Do not mark work complete just because a screen exists.
