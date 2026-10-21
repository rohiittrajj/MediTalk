# Project status

Status: initial repository foundation.

## Present in starter
- [x] Product and engineering documentation.
- [x] Persistent agent instructions.
- [x] Next.js frontend shell.
- [x] FastAPI health endpoint and test.
- [x] PostgreSQL Docker Compose configuration.
- [x] Environment template and ignore rules.
- [x] Phase 1 Clinical Tools (`apps/agent/`):
  - [x] Deterministic emergency red-flag screener (`screen_red_flags`)
  - [x] Structured clinical entity extractor (`extract_clinical_facts`) with provenance tracking
  - [x] Chronological timeline sequencer and conflict detector (`detect_conflicts_and_timeline`)
  - [x] Clinical preparation draft synthesizer (`synthesize_clinical_draft`) with mandatory clinician review notices
  - [x] Comprehensive standalone test suite (28 passing tests in `apps/agent/tests/`)
- [x] Phase 2 Agent Chat Protocol Adapter (`apps/agent/`):
  - [x] Official ACP specification compliance (`chat_protocol_spec`, `ChatMessage`, `ChatAcknowledgement`, `TextContent`)
  - [x] Multi-turn per-sender conversational state isolation
  - [x] Purpose-specific consent enforcement prior to intake
  - [x] Permanent emergency red-flag state tracking across dialogue turns
  - [x] Malformed, empty, and unsupported input handling without crashing
  - [x] Live agent initialization verified with official `uagents` runtime (`agent1...`)
  - [x] Standalone and pytest suites expanded to 40 passing tests (0 failures)
- [x] Phase 3 Agentverse Registration & Deployment Readiness (`apps/agent/`):
  - [x] Automated single-file bundle compiler (`apps/agent/deploy/build_bundle.py`) enforcing `apps/agent/src/` as single source of truth
  - [x] Self-contained Agentverse Hosted Agent bundle (`apps/agent/deploy/agentverse_bundle.py`) with zero dependencies outside `uagents`
  - [x] In-memory bundle execution test suite (`apps/agent/tests/test_bundle.py`) verifying full clinical intake workflow
  - [x] Both Hosted Agent and Local Mailbox deployment paths fully documented in `apps/agent/README.md`
  - [x] End-to-end ASI:One verification scenarios and transcripts documented for happy path and emergency escalation
  - [x] All 41 unit and integration tests passing in both standalone runner and pytest suites

## Not implemented
- [ ] Authentication/authorization
- [ ] Patient cases and migrations
- [ ] Consent workflow
- [ ] Adaptive conversational intake
- [ ] Speech provider
- [ ] Red-flag rules and live staff routing
- [ ] Document upload/OCR/extraction/review
- [ ] Timeline/provenance
- [ ] Summary generation and clinician workspace
- [ ] AYUSH assessment
- [ ] ABHA/ABDM/FHIR/HIS/EMR integrations
- [ ] End-to-end tests, security review, production deployment

## Limitations
This is not a complete healthcare application. The exact OneService palette has not been verified. External services are not configured. Authentication and authorization must be implemented before real patient data is used.

Only mark features complete after implementation and verification. Record test commands/results when updating this file.

### Verification Record
- **Date:** 2026-10-20
- **Commands:**
  - Standalone runner: `python apps/agent/tests/runner.py` -> 41 passed, 0 failed.
  - Virtualenv pytest: `pytest apps/agent/tests -v` -> 41 passed in 3.53s, 0 failed, 0 warnings.
  - Bundle in-memory verification: `python apps/agent/tests/test_bundle.py` -> PASSED.
- **Coverage:** Emergency warning screening (cardiac, stroke, respiratory, anaphylaxis, hemorrhage, crisis), extraction with missing-field preservation, overlapping lab span deduplication, medication dosage conflict detection, allergy statement contradiction detection, safety state persistence across multi-turn sessions, clinical draft synthesis with provenance, ACP message parsing, receipt acknowledgement generation, consent enforcement, sender state isolation, conversational error recovery, live ACP message handler execution, live uAgent initialization (`agent1qf2n5ygzhfp5fkygekwsy5fd6m9qsmyudl65lksq4xjekhngentpulkk2sl`), and self-contained Agentverse bundle execution with full dialogue cycle.
