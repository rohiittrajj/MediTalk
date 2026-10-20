# Product requirements

## Purpose
Prepare a structured, source-aware patient history by combining an accessible guided interview with information extracted from existing medical documents. A qualified clinician reviews and approves the draft. MediTalk does not autonomously diagnose or prescribe.

## Users
- Patient: provides history, consent, and documents; can correct misunderstandings.
- Clinician: reviews, edits, accepts, or rejects the generated history.
- Authorized staff: assists with intake and responds to urgent alerts.
- Administrator: manages configuration and authorized users under least-privilege access.

## End-to-end workflow
1. Identify/start a patient case using the configured identity workflow.
2. Explain data use accessibly and obtain purpose-specific consent.
3. Select language and interaction mode.
4. Ask adaptive medical-history questions; support voice where available and touch/text as a reliable alternative.
5. Evaluate explicit emergency red-flag rules and route urgent concerns to human help.
6. Upload medical documents and extract supported clinical facts.
7. Build a dated timeline while showing uncertainty and contradictions.
8. Generate a structured draft with source provenance and missing-data indicators.
9. Allow patient recap/correction where implemented.
10. Route the draft to an authorized clinician for editing, acceptance, rejection, or return for correction.
11. Store the resulting record with audit history and transmit externally only through a real, authorized, tested integration.

## Required capabilities
### Patient intake
- English and Hindi as initial languages.
- Voice and touch/text options; speech support must degrade gracefully if unsupported or permission is denied.
- Adaptive follow-up based on chief complaint and previous answers.
- Capture chief complaint/HPI, relevant past medical/surgical history, medications, allergies, family/personal history, review of systems, and prior investigations.
- Distinguish unknown, not provided, and declined answers.

### AYUSH assessment
Offer an explicit AYUSH workflow with configurable relevant fields for Prakriti, Vikriti, Agni, Koshtha, Ahara-Vihara, Nidana, Samprapti, Trividha Pariksha, Ashtavidha Pariksha, and Dashavidha Pariksha. Do not force these fields on every patient or fabricate missing values.

### Emergency red flags
Document and test explicit rules for urgent presentations, including chest pain with breathing difficulty and sudden stroke-like symptoms. Escalate to human staff only if a real monitored destination is configured. Otherwise show clear instructions to seek local emergency help. Absence of a trigger never rules out an emergency.

### Document intelligence
Accept validated images and PDFs with file size/type limits. Extract supported diagnoses, medications/dosages, laboratory values/units/reference ranges, dates, procedures, and source references. Show extraction status, confidence, ambiguous fields, and review controls. OCR must not silently infer missing units or dosages.

### Timeline and summary
Build a chronological view of encounters, documents, medications, and investigations. Preserve conflicting values for review. The structured summary should cover complaint/HPI, relevant history, medications/allergies, family/personal history, review of systems, investigations, and AYUSH fields when selected. Identify whether each fact is patient-reported, document-extracted, clinician-entered, or generated/normalized.

### Clinician workspace
Authorized case queue, urgency flags, document review, timeline, summary editing, accept/reject/return actions, and audit events. Enforce authorization on the server.

### Consent, privacy, and interoperability
Purpose-specific consent, withdrawal handling, data minimization, access control, auditability, retention/deletion policy, and private document storage. ABHA/ABDM, FHIR, and HIS/EMR are not considered operational until an authorized end-to-end integration is tested. Clearly label sandbox workflows.

## Non-functional requirements
Responsive kiosk/tablet/desktop layout; accessible keyboard and touch interactions; clear loading/error/success states; secure secret handling; structured logs without clinical content; migrations, backups, automated tests, and synthetic-only development data.

## Acceptance rule
A feature is done only when the normal path, failure states, authorization, relevant tests, accessibility, and documentation are verified—not merely when its UI exists.
