# Testing strategy

## Backend
Use Pytest for schema validation, authorization, state transitions, audit events, red-flag rules, document extraction, provenance, and failure cases. Red-flag rules require qualified clinical review. Use synthetic document fixtures.

## Frontend
Use Vitest and React Testing Library for accessible labels, keyboard behavior, validation, workflow states, loading/errors, microphone permission denial, and unsupported speech.

## End-to-end
Use Playwright to test: consent and case start; intake by touch/text; speech where supported; urgent red-flag handling; synthetic document upload and extraction status; source-aware summary; clinician edit/approval; rejection of unauthorized access; and external integration failures not appearing successful.

## Quality gates
Run relevant unit/integration tests, frontend lint/typecheck/build, backend lint/typecheck/tests. Record actual commands and outcomes. Passing tests do not replace clinical, privacy, security, or accessibility review.
