# Architecture

## Initial stack and boundaries
- `apps/web`: Next.js App Router, React, TypeScript; patient and clinician UI.
- `apps/api`: FastAPI, Python, Pydantic; business rules, authorization, persistence, orchestration, and adapters.
- PostgreSQL: structured records and workflow state.
- Private object-storage adapter: uploaded documents; local development implementation first.
- Provider adapters: speech, OCR, language processing, identity, and healthcare-system exchange.

Keep secrets and trusted clinical decisions out of browser code.

## Logical modules
Identity/access; consent; patient cases/encounters; intake sessions/questionnaires; speech; document upload/OCR/extraction/review; clinical facts and provenance; timeline/conflict detection; summary generation/review; red-flag rules/escalation; audit; interoperability.

## Data flow
Validate request -> authenticate and authorize -> verify required consent -> store intake/document job -> extract candidate facts with provenance/confidence -> generate draft with missing/conflicting data marked -> clinician reviews -> record audit event -> optionally transmit through an authorized integration adapter.

## Suggested entities
User, Role, Patient, PatientCase, Encounter, ConsentRecord, IntakeSession, QuestionnaireResponse, UploadedDocument, ExtractionJob, ClinicalFact, SummaryDraft, ClinicianReview, RedFlagEvent, AuditEvent, ExternalTransmission.

Use stable IDs, explicit statuses, timestamps, constraints, and migrations. Keep source documents separate from normalized facts.

## Provenance
Where applicable, store source type, source record/page, extraction or generation time, confidence/review state, and reviewer/correction history. Do not silently overwrite conflicting values.

## API conventions
Use versioned routes such as `/api/v1/`; Pydantic validation; consistent errors; bounded uploads; pagination; idempotency for external transmission; no stack traces in client responses. Add authentication and authorization before exposing clinical records.

## Background jobs and deployment
Begin with an abstract processing interface and explicit job states. Add a worker/queue when justified by latency or reliability. Production requires managed secrets, HTTPS, private storage, restricted database networking, backups, monitoring, retention policy, and incident response. Starter configuration is not production-hardened.
