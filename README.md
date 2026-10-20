# MediTalk

MediTalk is a patient-history intelligence and clinical preparation platform. It helps patients share medical history through accessible voice and touch interactions, organizes information from medical documents, and prepares a structured history for clinician review.

MediTalk does not autonomously diagnose or prescribe and does not replace qualified healthcare professionals.

## Initial stack
- Frontend: Next.js App Router, React, TypeScript
- API: Python, FastAPI, Pydantic
- Database: PostgreSQL; SQLAlchemy and Alembic planned
- Tests: Pytest, Vitest/Testing Library, Playwright
- External speech, OCR, language-processing, identity, and hospital integrations must use provider adapters.

## Local development
1. Install Node.js 20+, Python 3.11+, and Docker.
2. Copy `.env.example` to `.env`.
3. Start PostgreSQL: `docker compose up -d db`
4. API: `cd apps/api`, create/activate a virtual environment, run `pip install -e ".[dev]"`, then `uvicorn app.main:app --reload --port 8000`.
5. Frontend: `cd apps/web`, run `npm install`, then `npm run dev`.
6. Open `http://localhost:3000`; API health check: `http://localhost:8000/health`.

This is a starter foundation, not a complete healthcare application. Never use real patient data in development.

## Source of truth
Read `AGENTS.md` and the documents in `docs/` before implementing features.
