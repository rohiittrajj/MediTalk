# Persistent coding-agent instructions

Read this file, `README.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY_AND_PRIVACY.md`, `docs/DESIGN_SYSTEM.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING.md`, and `docs/PROJECT_STATUS.md` before substantial work.

## Product and brand
- Product name: MediTalk. Present it as a standalone healthcare product. Do not mention competitions, challenge names, or submission processes in product UI or product documentation.
- Design should be clean, practical, humane, and accessible. No neon, glowing effects, sci-fi patterns, or generic AI-dashboard styling.
- The intended palette is inspired by the user's OneService project. Do not guess exact colors. Inspect source assets if provided; otherwise keep tokens centralized and mark exact palette as pending verification.

## Engineering rules
- Build connected end-to-end workflows, not disconnected mock screens.
- Use strict TypeScript and typed Python. Validate inputs at API boundaries.
- Keep sensitive-data access and clinical business rules on the server.
- Use database migrations for schema changes.
- Never commit secrets, patient documents, raw audio, database dumps, or real patient data.
- Preserve provenance: distinguish patient-reported, document-extracted, clinician-entered, and generated content.
- Never invent missing clinical facts, units, dates, or dosages. Surface conflicts and low confidence for review.
- A generated summary remains a draft until an authorized clinician reviews and accepts it.
- Red-flag rules must be explicit and tested. Do not imply that no alert means no emergency.
- External services must be accessed through adapters. Never fake a successful external submission. Label sandbox/demo mode honestly.
- Do not claim compliance, security verification, integration, or feature completion without evidence.

## Definition of done
1. Implement the requested behavior, not just a plan or placeholder.
2. Add/update tests and run relevant tests, type checks, lint, and builds.
3. Handle success, loading, empty, invalid, permission-denied, and failure states.
4. Update documentation and `docs/PROJECT_STATUS.md`.
5. Report what changed, which commands actually ran, results, limitations, and next step.
6. Follow the dependency order in `docs/IMPLEMENTATION_PLAN.md`; inspect existing code before changing it.
