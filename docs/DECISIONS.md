# Architecture decisions

## ADR-001: Next.js + TypeScript frontend and FastAPI backend
**Status:** Accepted. Next.js supports accessible responsive interfaces; Python is useful for document processing and AI integrations. Trade-off: two runtimes and explicit API contracts are required.

## ADR-002: PostgreSQL for structured data
**Status:** Accepted. Patient cases, consent, extracted facts, review states, and audit events are relational. Use SQLAlchemy and Alembic when persistence is implemented.

## ADR-003: Provider adapters
**Status:** Accepted. Speech, OCR, language processing, identity, and healthcare exchange must be isolated behind adapters to improve testing and provider replacement.

## ADR-004: Verify visual tokens
**Status:** Accepted. Centralize theme tokens and do not claim OneService palette matching until source assets have been inspected.
