/* =========================================================
   MediKiosk — chat.js
   AI Case-Taking (Converse Step)
   Structured symptom intake + Real-time Red-Flag detection +
   Conversational agent with integrated Web Speech API mic
   ========================================================= */

'use strict';

// ── Conversational Demo Replies ───────────────────────────
const CASE_RESPONSES = [
  {
    keywords: ['chest', 'heart', 'tightness', 'left arm', 'heaviness', 'pressure'],
    reply: `⚠️ **Red-Flag Warning Noted:** Chest tightness or discomfort can be an indicator of acute cardiac compromise. I have flagged this as a Priority-1 triage item for your attending physician.\n\n• Does the discomfort radiate to your jaw, neck, or left arm?\n• Do you have accompanying breathlessness, nausea, or cold sweating?\n• If severe, please inform the triage desk or call 112 immediately.`
  },
  {
    keywords: ['breath', 'breathing', 'shortness of breath', 'gasping'],
    reply: `I have recorded your respiratory symptoms. Shortness of breath on exertion is an essential clinical finding.\n\n• Did this start suddenly or build up over days?\n• Do you experience wheezing sounds or cough up colored phlegm?\n• Does propping up pillows help you breathe easier at night?`
  },
  {
    keywords: ['fever', 'bukhar', 'temperature', 'chills', 'thand'],
    reply: `Noted your fever symptoms in your clinical record.\n\n• What was the highest temperature recorded with a thermometer?\n• Are there chills, shivering, or burning during urination?\n• Any joint aches or skin rashes noticed?`
  },
  {
    keywords: ['cough', 'khansi', 'throat', 'gala'],
    reply: `I've documented your cough. To help the clinician evaluate:\n\n• Is the cough predominantly dry or productive with sputum?\n• Is it more severe during early mornings or late night?\n• Have you taken any cough lozenges or syrup so far?`
  },
  {
    keywords: ['medicine', 'medication', 'dawai', 'tablet', 'dose'],
    reply: `I have updated your active medications list. Please specify if you take these daily or only when symptoms arise, and whether a physician previously prescribed them.`
  },
  {
    keywords: ['allergy', 'reaction', 'rash'],
    reply: `Allergy alert recorded. This will be prominently marked in amber on your clinical sheet to prevent unsafe prescriptions by the doctor.`
  }
];

const DEFAULT_REPLY = `Thank you for sharing that symptom detail. I have documented it into your clinical intake session. Your attending doctor will review this timeline before examining you.\n\nYou can also click the quick chips on the left or use the microphone to add more context.`;

// ── DOM References ────────────────────────────────────────
const messagesEl       = document.getElementById('chatMessages');
const inputEl          = document.getElementById('chatInput');
const sendBtn          = document.getElementById('sendBtn');
const micBtn           = document.getElementById('micBtnChat');
const voiceStatusBadge = document.getElementById('voiceStatusBadge');
const voiceStatusText  = document.getElementById('voiceStatusText');
const clearBtn         = document.getElementById('clearChatBtn');

const chiefInput       = document.getElementById('caseChiefComplaint');
const durationVal      = document.getElementById('caseDurationVal');
const durationUnit     = document.getElementById('caseDurationUnit');
const severitySlider   = document.getElementById('caseSeverity');
const severityDisplay  = document.getElementById('caseSeverityDisplay');
const symptomNotes     = document.getElementById('caseSymptomNotes');
const currentMeds      = document.getElementById('caseCurrentMeds');
const allergiesInput   = document.getElementById('caseAllergies');
const caseForm         = document.getElementById('caseTakingForm');
const saveDraftBtn     = document.getElementById('saveCaseDraftBtn');
const redFlagAlertBox  = document.getElementById('caseTakingRedFlagAlert');

// Speech Recognition instance
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;

document.addEventListener('DOMContentLoaded', () => {
  loadExistingCaseData();
  setupQuestionnaireEvents();
  setupChatEvents();
  setupVoiceInput();
  checkAndShowRedFlags();
});

// ── 1. Prepopulate existing data ──────────────────────────
function loadExistingCaseData() {
  const patient = MediKioskData.getCurrentPatient();
  if (!patient) return;

  const demo = patient.demographics || {};
  const ct = patient.caseTaking || {};

  const nameEl = document.getElementById('activePatNameDisplay');
  if (nameEl) nameEl.textContent = demo.fullName || 'Patient Intake';

  if (chiefInput && ct.chiefComplaint) chiefInput.value = ct.chiefComplaint;
  if (durationVal && ct.durationValue) durationVal.value = ct.durationValue;
  if (durationUnit && ct.durationUnit) durationUnit.value = ct.durationUnit;

  if (severitySlider && ct.severity !== undefined) {
    severitySlider.value = ct.severity;
    updateSeverityDisplay(ct.severity);
  }

  if (symptomNotes && ct.symptomNotes) symptomNotes.value = ct.symptomNotes;
  if (currentMeds && ct.currentMedications) currentMeds.value = ct.currentMedications;
  if (allergiesInput && ct.allergies) allergiesInput.value = ct.allergies;

  // Check symptom checkboxes
  const syms = ct.symptoms || [];
  document.querySelectorAll('.sym-checkbox').forEach(cb => {
    if (syms.includes(cb.value) || syms.some(s => s.toLowerCase().includes(cb.value.toLowerCase().split(' ')[0]))) {
      cb.checked = true;
    }
  });

  // Welcome message in chat
  appendMessage(
    `Hello **${escapeHtml(demo.fullName || 'Patient')}**! I am your MediKiosk AI Case-Taking assistant.\n\nPlease describe your primary symptom or use the questionnaire on the left. You can also tap the microphone to speak in English or Hindi.`,
    'assistant'
  );
}

// ── 2. Questionnaire Events ───────────────────────────────
function setupQuestionnaireEvents() {
  // Severity Slider live change
  if (severitySlider) {
    severitySlider.addEventListener('input', () => {
      updateSeverityDisplay(severitySlider.value);
      checkAndShowRedFlags();
    });
  }

  // Quick Chips
  document.querySelectorAll('.quick-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      if (chiefInput) {
        chiefInput.value = chip.getAttribute('data-text');
        checkAndShowRedFlags();
      }
    });
  });

  // Live Red Flag checking on chief input & checkboxes
  if (chiefInput) {
    chiefInput.addEventListener('input', () => checkAndShowRedFlags());
  }
  document.querySelectorAll('.sym-checkbox').forEach(cb => {
    cb.addEventListener('change', () => checkAndShowRedFlags());
  });

  // Save Draft button
  if (saveDraftBtn) {
    saveDraftBtn.addEventListener('click', () => {
      saveCaseData();
      MediTalk.showToast('Case-taking symptoms draft saved.', 'success');
    });
  }

  // Form Submit -> Next Step
  if (caseForm) {
    caseForm.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!chiefInput.value.trim()) {
        MediTalk.showToast('Please state your primary chief complaint.', 'warning');
        chiefInput.focus();
        return;
      }
      saveCaseData();
      MediTalk.showToast('Symptoms recorded! Moving to Step 3: Document Scan.', 'success');
      setTimeout(() => {
        window.location.href = 'image-analysis.html';
      }, 400);
    });
  }
}

function updateSeverityDisplay(val) {
  if (!severityDisplay) return;
  const num = Number(val);
  severityDisplay.textContent = `${num} / 10`;

  if (num >= 8) {
    severityDisplay.className = 'badge bg-danger fs-6';
  } else if (num >= 5) {
    severityDisplay.className = 'badge bg-warning text-dark fs-6';
  } else {
    severityDisplay.className = 'badge bg-success fs-6';
  }
}

function getSelectedSymptoms() {
  const list = [];
  document.querySelectorAll('.sym-checkbox:checked').forEach(cb => {
    list.push(cb.value);
  });
  return list;
}

function saveCaseData() {
  const patient = MediKioskData.getCurrentPatient();
  if (!patient) return;

  const chief = chiefInput ? chiefInput.value.trim() : '';
  const durVal = durationVal ? durationVal.value.trim() : '';
  const durUnit = durationUnit ? durationUnit.value : 'days';
  const sev = severitySlider ? Number(severitySlider.value) : 5;
  const notes = symptomNotes ? symptomNotes.value.trim() : '';
  const meds = currentMeds ? currentMeds.value.trim() : '';
  const allergies = allergiesInput ? allergiesInput.value.trim() : '';
  const syms = getSelectedSymptoms();

  // Run red flags detection
  const redFlagCheck = MediKioskData.detectRedFlags(chief + ' ' + notes, syms, sev);

  patient.caseTaking = {
    chiefComplaint: chief,
    durationValue: durVal,
    durationUnit: durUnit,
    severity: sev,
    symptoms: syms,
    symptomNotes: notes,
    pastMedicalHistory: patient.caseTaking?.pastMedicalHistory || [],
    pastHistoryNotes: patient.caseTaking?.pastHistoryNotes || '',
    currentMedications: meds,
    allergies: allergies || 'No Known Drug Allergies (NKDA)',
    redFlagsDetected: redFlagCheck.redFlags,
    redFlagStatus: redFlagCheck.severityStatus
  };

  patient.workflowStep = Math.max(patient.workflowStep || 1, 3);
  MediKioskData.saveCurrentPatient(patient);
}

// ── 3. Real-Time Red Flag Engine ──────────────────────────
function checkAndShowRedFlags() {
  if (!redFlagAlertBox) return;

  const chief = chiefInput ? chiefInput.value : '';
  const notes = symptomNotes ? symptomNotes.value : '';
  const syms = getSelectedSymptoms();
  const sev = severitySlider ? Number(severitySlider.value) : 5;

  const result = MediKioskData.detectRedFlags(chief + ' ' + notes, syms, sev);

  if (result.hasRedFlags) {
    redFlagAlertBox.style.display = 'block';
    redFlagAlertBox.innerHTML = `
      <div class="red-flag-banner" role="alert">
        <i class="bi bi-exclamation-triangle-fill" style="font-size:1.6rem;flex-shrink:0;"></i>
        <div>
          <strong style="font-size:.95rem;">⚠️ POTENTIAL EMERGENCY RED-FLAG DETECTED:</strong>
          <ul class="mb-1 ps-3" style="font-size:.84rem;">
            ${result.redFlags.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
          </ul>
          <span style="font-size:.78rem;">Please seek immediate in-person triage if feeling dizzy, crushing chest pain, or breathless.</span>
        </div>
      </div>
    `;
  } else {
    redFlagAlertBox.style.display = 'none';
    redFlagAlertBox.innerHTML = '';
  }
}

// ── 4. Chat Events ────────────────────────────────────────
function setupChatEvents() {
  if (sendBtn && inputEl) {
    sendBtn.addEventListener('click', handleUserSend);
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleUserSend();
      }
    });
  }

  if (clearBtn && messagesEl) {
    clearBtn.addEventListener('click', () => {
      messagesEl.innerHTML = '';
      loadExistingCaseData();
      MediTalk.showToast('Chat history cleared.', 'info');
    });
  }
}

function handleUserSend() {
  const text = inputEl.value.trim();
  if (!text) return;

  appendMessage(text, 'user');
  inputEl.value = '';

  // If chief complaint is empty, fill it with user text
  if (chiefInput && !chiefInput.value.trim()) {
    chiefInput.value = text;
    checkAndShowRedFlags();
  }

  // Generate demo response
  setTimeout(() => {
    const reply = findBestReply(text);
    appendMessage(reply, 'assistant');
    checkAndShowRedFlags();
  }, 450);
}

function findBestReply(userText) {
  const lower = userText.toLowerCase();
  for (const item of CASE_RESPONSES) {
    if (item.keywords.some(kw => lower.includes(kw))) {
      return item.reply;
    }
  }
  return DEFAULT_REPLY;
}

function appendMessage(content, role) {
  if (!messagesEl) return;
  const wrap = document.createElement('div');
  wrap.style.display = 'flex';
  wrap.style.flexDirection = 'column';
  wrap.style.alignItems = role === 'user' ? 'flex-end' : 'flex-start';

  const bubble = document.createElement('div');
  bubble.className = `msg-bubble msg-${role}`;
  bubble.innerHTML = role === 'user' ? escapeHtml(content) : renderMarkdown(content);

  const timeEl = document.createElement('span');
  timeEl.className = 'msg-time';
  timeEl.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  wrap.appendChild(bubble);
  wrap.appendChild(timeEl);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
}

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── 5. Integrated Voice Input (Web Speech API) ─────────────
function setupVoiceInput() {
  if (!micBtn) return;

  if (!SpeechRecognition) {
    micBtn.title = 'Speech recognition not supported in this browser.';
    micBtn.style.opacity = '0.5';
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-IN'; // Default to Indian English / Hindi accent

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add('btn-danger');
    micBtn.classList.remove('btn-outline-primary');
    if (voiceStatusBadge) voiceStatusBadge.style.setProperty('display', 'flex', 'important');
    if (voiceStatusText) voiceStatusText.innerHTML = '<i class="bi bi-soundwave text-danger me-1"></i> Listening to your symptoms...';
  };

  recognition.onresult = (e) => {
    let transcript = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      transcript += e.results[i][0].transcript;
    }
    if (inputEl) inputEl.value = transcript;
  };

  recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove('btn-danger');
    micBtn.classList.add('btn-outline-primary');
    if (voiceStatusBadge) voiceStatusBadge.style.setProperty('display', 'none', 'important');

    if (inputEl && inputEl.value.trim()) {
      handleUserSend();
    }
  };

  recognition.onerror = (e) => {
    isListening = false;
    micBtn.classList.remove('btn-danger');
    micBtn.classList.add('btn-outline-primary');
    if (voiceStatusBadge) voiceStatusBadge.style.setProperty('display', 'none', 'important');
    console.warn('Speech recognition error:', e.error);
    if (e.error !== 'no-speech') {
      MediTalk.showToast(`Microphone notice: ${e.error}`, 'warning');
    }
  };

  micBtn.addEventListener('click', () => {
    if (isListening) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (err) {
        console.error('Recognition start error:', err);
      }
    }
  });
}
