# Security, privacy, and clinical safety

This is an engineering baseline, not a legal compliance certification.

## Data and consent
Explain purposes, data categories, processing, sharing, and retention before optional sensitive collection. Record consent purpose/version/time and withdrawal where applicable. Minimize collection and avoid retaining raw audio by default. Use synthetic data for development.

## Application security
Implement server-side authentication and role/case authorization before real clinical use. Validate inputs; restrict upload types/sizes/rates; store documents privately; use HTTPS in deployment; protect secrets with environment/secret management; prevent injection, XSS, CSRF where applicable, insecure direct object references, and unsafe file handling. Encrypt storage/backups according to deployment needs.

## Logging and audit
Audit security-relevant access and workflow transitions. Never log patient narratives, document text, credentials, or full sensitive request bodies. Restrict audit access and define retention.

## Clinical integrity
Preserve provenance for patient-reported, document-extracted, clinician-entered, and generated content. Mark uncertainty and conflicts. Never invent missing facts or silently infer units/dosages. Drafts require clinician review. Red-flag rules must be transparent, tested, and reviewed by qualified clinical stakeholders; no alert does not mean no emergency.

## Providers and integrations
Review privacy terms, retention, processing location, and security controls before sending sensitive data to AI/OCR/speech providers. ABHA/ABDM/FHIR/HIS/EMR integrations must not be described as operational until authorized and tested end-to-end. Obtain qualified review for applicable legal obligations; do not claim compliance just because controls are documented.

## Emergency handling
Show clear local emergency instructions on urgent red flags. Claim staff routing only when a real monitored destination is configured. Never imply the application replaces emergency assessment.
