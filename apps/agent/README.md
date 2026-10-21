# MediTalk Clinical Preparation Agent

The **MediTalk Clinical Preparation Agent** is an autonomous, discoverable clinical intake and history preparation agent.

It runs natively on the Fetch.ai decentralized agent network via the **Agent Chat Protocol (ACP)** and interacts directly with patients inside **ASI:One** conversations without requiring an external web frontend.

> **CLINICAL SAFETY MANDATES:**
> - **MediTalk does NOT autonomously diagnose, treat, or prescribe.**
> - All generated summaries remain unverified drafts until reviewed and accepted by an authorized clinician.
> - Emergency warning screening is rule-based and non-exhaustive; absence of an alert never rules out an emergency.
> - Never invent missing facts, dosages, units, or dates.
> - Preserves provenance across patient-reported, document-extracted, and clinician-entered data.
> - Explicit informed consent is mandatory prior to clinical intake.
> - Emergency state persists permanently across the entire intake session.

---

## Architecture & Tools

The agent package exposes deterministic, source-aware clinical tools and an ACP network adapter:

| Tool | Function | Purpose |
| :--- | :--- | :--- |
| **Emergency Screener** | `screen_red_flags(text)` | Evaluates inputs against configured high-risk emergency warning patterns (cardiac, stroke, respiratory, anaphylaxis, hemorrhage, crisis). |
| **Fact Extractor** | `extract_clinical_facts(text, source_type, source_ref)` | Extracts medications, dosages, units, frequencies, conditions, allergies (including NKDA), and laboratory values with provenance. |
| **Timeline & Conflict Detector** | `detect_conflicts_and_timeline(facts)` | Orders dated events chronologically and flags conflicting medication dosages, contradictory allergy statements, and missing units/dates. |
| **Draft Synthesizer** | `synthesize_clinical_draft(session)` | Compiles a structured, provenance-tagged clinical preparation draft for clinician review with missing information checklists. |
| **ACP Protocol Adapter** | `create_agent()`, `on_chat_message()` | Integrates with Fetch.ai `chat_protocol_spec` for live dialogue inside ASI:One. |
| **Turn Processor** | `process_user_turn(sender, text)` | Per-sender state machine enforcing consent, continuous safety screening, conflict alerting, and summary generation. |

---

## Directory Structure

```
apps/agent/
├── .env.example                 # Agent network environment template
├── pyproject.toml               # Package dependencies (pydantic, uagents, pytest, ruff)
├── README.md                    # Complete setup, deployment, and verification guide
├── deploy/
│   ├── README.md                # Deployment overview
│   ├── build_bundle.py          # Automated compiler: src/ -> single-file bundle
│   └── agentverse_bundle.py     # Self-contained Agentverse Hosted Agent bundle
├── src/
│   ├── __init__.py              # Public package exports
│   ├── agent.py                 # uAgents + Agent Chat Protocol (ACP) entrypoint
│   ├── session.py               # Conversational intake state machine & turn processor
│   ├── models.py                # Domain models, provenance records, and data contracts
│   ├── red_flags.py             # Emergency red-flag safety screening
│   ├── extractor.py             # Deterministic clinical entity extractor
│   ├── timeline.py              # Chronological sequencer & conflict detector
│   ├── summary.py               # Structured clinical draft synthesizer
│   └── tools.py                 # Unified tool facade
└── tests/
    ├── __init__.py
    ├── runner.py                # Standalone test runner (zero external dependencies)
    ├── test_acp_adapter.py      # ACP message parsing, ack/reply, consent, isolation tests
    ├── test_bundle.py           # In-memory execution verification of deployment bundle
    ├── test_red_flags.py        # Safety screening tests (emergency vs non-urgent)
    ├── test_extractor.py        # Extraction tests (doses, units, labs, NKDA)
    ├── test_timeline.py         # Conflict & timeline tests (dosage clashes, NKDA conflict)
    ├── test_summary.py          # Draft synthesis & safety banner tests
    └── test_safety_and_provenance.py  # Safety persistence & provenance integrity tests
```

---

## Single Source of Truth Mandate

All active development is maintained in modular files under `apps/agent/src/`. 

To maintain parity with the Agentverse Hosted Agent browser editor, `apps/agent/deploy/build_bundle.py` compiles `src/` into a single standalone script:

```bash
# Re-generate the Agentverse deployment bundle:
python apps/agent/deploy/build_bundle.py
```

Never edit `apps/agent/deploy/agentverse_bundle.py` directly.

---

## Deployment Options

### Option A: Agentverse Hosted Agent (Recommended for 24/7 Availability)

Running MediTalk as an Agentverse Hosted Agent allows it to remain online 24/7 on Fetch.ai's cloud without needing a local process or machine running.

#### Step-by-Step Instructions:
1. **Log in to Agentverse:**
   - Navigate to [https://agentverse.ai](https://agentverse.ai) and sign in.
2. **Create a New Agent:**
   - In the sidebar, click **Agents** -> **+ New Agent**.
   - Select **Blank Agent**.
   - Name the agent (e.g., `meditalk-clinical-agent`).
3. **Deploy the Code Bundle:**
   - Open the web code editor for your agent.
   - Select all existing template code and delete it.
   - Copy the full contents of `apps/agent/deploy/agentverse_bundle.py` from this repository.
   - Paste it into the Agentverse editor.
4. **Start the Agent:**
   - Click the **Start** button in the upper right.
   - Wait for the console log to confirm: `Starting MediTalk Agent agent1...`.
   - The agent publishes its ACP protocol manifest (`chat_protocol_spec`) automatically to the Almanac ledger with `publish_manifest=True`.
5. **Retrieve Your Agent Address:**
   - Note the agent address displayed at the top of the Agentverse console (starts with `agent1...`).
   - This address is your permanent, unique handle on ASI:One.

---

### Option B: Local Agent with Agentverse Mailbox

If you prefer to run the agent locally on your workstation while remaining reachable from ASI:One:

1. **Create a Mailbox on Agentverse:**
   - Go to [https://agentverse.ai](https://agentverse.ai) -> **Agents** -> **Local Agents** -> **+ New Local Agent**.
   - Select **Mailbox Agent** and provide a name.
   - Copy the generated Mailbox API key / Secret.
2. **Configure Environment:**
   ```bash
   cd apps/agent
   copy .env.example .env
   ```
   Open `.env` and set:
   ```env
   AGENT_NAME="meditalk_local_agent"
   AGENT_PORT=8001
   AGENT_MAILBOX_KEY="your-agentverse-mailbox-key-here"
   ```
3. **Start the Agent:**
   ```bash
   python -m apps.agent.src.agent
   ```
   The local agent will connect to the Agentverse mailbox server and poll for incoming ACP messages from ASI:One.

---

## ASI:One Verification & Testing Guide

Once registered and started, you can talk to MediTalk directly inside **ASI:One**:

1. Navigate to [https://asi1.ai](https://asi1.ai) and log in.
2. Search for your agent by its address (`agent1...`) or select it from your connected agents.
3. Open a new chat session.

### Verification Checklist:

- [ ] **Turn 1: Greeting & Informed Consent**
  - *User:* `Hello`
  - *MediTalk:* Welcomes the patient, explains boundaries (does not diagnose/prescribe, drafts require clinician review, not for emergencies), and asks for explicit consent.
- [ ] **Turn 2: Granting Consent**
  - *User:* `I consent`
  - *MediTalk:* Confirms consent recorded, transitions state to active intake, and prompts for chief complaint / medical history.
- [ ] **Turn 3: History & Prescriptions Intake**
  - *User:* `I have Type 2 Diabetes and Hypertension. I take Metformin 500mg twice daily and Lisinopril 10mg daily. Allergic to Penicillin: skin rash.`
  - *MediTalk:* Acknowledges extracted conditions, medications with dosages/frequencies, and allergies with provenance.
- [ ] **Turn 4: Conflicting Data Detection**
  - *User:* `Actually my doctor increased my Lisinopril to 20mg daily.`
  - *MediTalk:* Detects the conflicting active dosages (`10mg` vs `20mg`), issues a warning alert, and flags it for clinician verification.
- [ ] **Turn 5: Emergency Screening & Persistent Escalation**
  - *User:* `I suddenly have severe crushing chest pain and shortness of breath.`
  - *MediTalk:* Detects cardiac red flags, issues a **CRITICAL EMERGENCY ALERT**, and advises immediate emergency services contact (911/112).
- [ ] **Turn 6: Emergency State Persistence**
  - *User:* `I also forgot to mention I take Aspirin.`
  - *MediTalk:* Retains the **PRIOR EMERGENCY ALERT** banner prominently across this turn and all subsequent turns.
- [ ] **Turn 7: Draft Synthesis**
  - *User:* `Prepare draft for my doctor`
  - *MediTalk:* Compiles a structured, provenance-tagged clinical preparation draft with sections for Chief Complaint, Identified Conflicts, Medications, Allergies, History, Timeline, Missing Items Checklist, and Clinician Acceptance fields.

---

## Example Conversation Transcripts

### 1. Happy Path: Intake & Clinical Preparation Draft

```markdown
User: Hello
MediTalk: 👋 **Welcome to MediTalk.**
I am a clinical preparation assistant designed to help you organize your medical history, medications, and records into a structured draft for your healthcare provider.

**Clinical Safety Notice & Limitations:**
- MediTalk does not autonomously diagnose conditions or prescribe medications.
- MediTalk does not provide emergency intervention. If you are experiencing an acute medical emergency, call emergency services immediately.
- All summaries are drafts that require review and verification by your clinician.

To begin, **do you consent** to sharing your health information for clinical preparation? (Reply **'Yes'** or **'I consent'** to proceed).

User: I consent.
MediTalk: ✅ **Consent Recorded.** Thank you.
Please tell me what brings you in today — what is your **main symptom or chief complaint**? You can also paste any prescriptions, discharge summaries, or laboratory test reports.

User: I am here for a routine checkup. I have high blood pressure and take Amlodipine 5mg daily. Also allergic to Sulfa drugs.
MediTalk: 📋 **Noted:** Medications: Amlodipine (5mg); Conditions: High Blood Pressure; Allergies: Sulfa.
Do you have any other symptoms, previous lab reports, or allergies to add? Or type **'summary'** when you are ready to generate your doctor's draft.

User: summary
MediTalk: Here is your structured clinical preparation draft for your doctor:

# MEDITALK CLINICAL PREPARATION DRAFT
> **IMPORTANT NOTICE FOR CLINICIANS:**
> This document is a structured intake draft compiled to assist clinical preparation.
> MediTalk does not autonomously diagnose, treat, or prescribe. All statements,
> extracted values, and detected conflicts must be reviewed and accepted by an authorized clinician.

**Status:** `DRAFT_PENDING_CLINICIAN_REVIEW`
Consent Status: Explicit patient consent recorded at `2026-10-20T22:00:00Z`

## 1. Chief Complaint & History of Present Illness (HPI)
**Chief Complaint:** I am here for a routine checkup.

## 2. Identified Clinical Conflicts & Discrepancies
No active contradictions or conflicting dosages detected across supplied inputs.

## 3. Medications
| Medication | Dosage | Frequency | Status | Source Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Amlodipine** | 5 mg | Daily | Active | `patient_reported` |

## 4. Allergies & Adverse Reactions
- **Sulfa** (`patient_reported`)

## 5. Diagnoses & Medical History
- **High Blood Pressure** (Status: *active*, Source: `patient_reported`)

## 8. Missing Information & Clinical Verification Checklist
- [ ] Routine clinical verification of baseline vitals.

---
### Clinician Review & Acceptance
- [ ] **Clinician Signature / Acceptance:** ___________________________
- [ ] **Date Reviewed:** ___________________________
- [ ] **Action:** `[ ] Accept with edits` | `[ ] Accept as is` | `[ ] Return for clarification`
```

---

### 2. Emergency Escalation Scenario

```markdown
User: I have crushing chest pain and I can't catch my breath.
MediTalk: 🚨 **CRITICAL EMERGENCY ALERT: High-risk warning signs were detected in the input: ACUTE_CHEST_PAIN_CARDIAC: Acute or crushing chest pain/pressure; SEVERE_RESPIRATORY_DISTRESS: Severe acute respiratory distress or inability to breathe**

👉 **Action Required:** SEEK IMMEDIATE EMERGENCY MEDICAL CARE. Call local emergency services (e.g., 911, 112, 108) or proceed immediately to the nearest hospital emergency room. MediTalk is a preparation tool and does not provide emergency intervention or diagnosis.

> *Rule-based safety screening only. The absence of a detected warning pattern does not rule out a medical emergency.*

User: I also take Metformin.
MediTalk: ⚠️ **PRIOR EMERGENCY ALERT:** Critical symptoms were previously detected during this intake. If you are experiencing acute distress, seek emergency medical care immediately.

---

📋 **Noted:** Medications: Metformin (dose unstated).
Do you have any other symptoms, previous lab reports, or allergies to add? Or type **'summary'** when you are ready to generate your doctor's draft.
```

---

## Running Automated Tests

All 41 tests can be run locally using the dedicated test environment:

```bash
# 1. Standalone test suite (standard library only):
python apps/agent/tests/runner.py

# 2. Pytest suite:
pytest apps/agent/tests -v
```

### Verified Test Results (41/41 passing):
- Emergency screener (cardiac, stroke, respiratory, anaphylaxis, hemorrhage, crisis patterns)
- Fact extractor (conditions, medications with dosages/frequencies, NKDA, laboratory values)
- Timeline and conflict detector (dosage discrepancy alerts, allergy contradictions)
- Draft synthesizer (structured Markdown, safety headers, clinician acceptance signature blocks)
- Safety & provenance integrity (emergency persistence, zero fabrication of missing units)
- ACP adapter (ChatMessage parsing, ChatAcknowledgement generation, multi-turn state isolation)
- Agentverse deployment bundle (in-memory syntax compilation and full dialogue execution)
