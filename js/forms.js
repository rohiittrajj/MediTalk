/* =========================================================
   MediKiosk — forms.js
   Patient Registration (Identify Step) + Staff Login
   Validation, ABHA Sandbox Simulated Verification, localStorage sync
   ========================================================= */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  initPatientRegistrationForm();
  initLoginForm();
});

// ── Shared helpers ────────────────────────────────────────
function fieldError(inputEl, msgEl, message) {
  if (inputEl) inputEl.classList.add('is-invalid');
  if (msgEl) { msgEl.textContent = message; msgEl.style.display = 'block'; }
}

function fieldClear(inputEl, msgEl) {
  if (inputEl) inputEl.classList.remove('is-invalid');
  if (msgEl) { msgEl.style.display = 'none'; }
}

function isValidPhone(phone) {
  const cleaned = phone.replace(/[^0-9]/g, '');
  return cleaned.length >= 10;
}

// ── PATIENT REGISTRATION FORM (IDENTIFY STEP) ─────────────
function initPatientRegistrationForm() {
  const form = document.getElementById('patientRegForm');
  if (!form) return;

  const nameInput   = document.getElementById('patName');
  const ageInput    = document.getElementById('patAge');
  const genderInput = document.getElementById('patGender');
  const phoneInput  = document.getElementById('patPhone');
  const abhaInput   = document.getElementById('patAbha');
  const langSelect  = document.getElementById('patLanguage');
  const emergName   = document.getElementById('patEmergName');
  const emergPhone  = document.getElementById('patEmergPhone');
  const histNotes   = document.getElementById('patHistoryNotes');
  const allergiesIn = document.getElementById('patAllergies');
  const consentBox  = document.getElementById('consentCheckbox');
  const verifyBtn   = document.getElementById('verifyAbhaBtn');
  const loadDemoBtn = document.getElementById('loadSamplePatientBtn');

  // Prepopulate from current patient if exists
  const current = MediKioskData.getCurrentPatient();
  if (current && current.demographics && current.demographics.fullName) {
    const d = current.demographics;
    if (nameInput) nameInput.value = d.fullName || '';
    if (ageInput) ageInput.value = d.age || '';
    if (genderInput) genderInput.value = d.gender || '';
    if (phoneInput) phoneInput.value = d.phone || '';
    if (abhaInput) abhaInput.value = d.abhaId || '';
    if (langSelect) langSelect.value = d.preferredLanguage || 'en';
    if (emergName) emergName.value = d.emergencyContactName || '';
    if (emergPhone) emergPhone.value = d.emergencyContactPhone || '';
    if (allergiesIn) allergiesIn.value = current.caseTaking?.allergies || '';
    if (consentBox) consentBox.checked = d.consentGiven || false;

    // Pre-check condition checkboxes
    const hist = current.caseTaking?.pastMedicalHistory || [];
    if (hist.some(h => h.includes('Hypertension'))) {
      const el = document.getElementById('histHypertension');
      if (el) el.checked = true;
    }
    if (hist.some(h => h.includes('Diabetes'))) {
      const el = document.getElementById('histDiabetes');
      if (el) el.checked = true;
    }
    if (hist.some(h => h.includes('Asthma'))) {
      const el = document.getElementById('histAsthma');
      if (el) el.checked = true;
    }
    if (hist.some(h => h.includes('Heart'))) {
      const el = document.getElementById('histHeart');
      if (el) el.checked = true;
    }
  }

  // Load Demo Patient handler
  if (loadDemoBtn) {
    loadDemoBtn.addEventListener('click', () => {
      if (nameInput) nameInput.value = 'Rajesh Kumar Verma';
      if (ageInput) ageInput.value = '46';
      if (genderInput) genderInput.value = 'Male';
      if (phoneInput) phoneInput.value = '+91 98765 43210';
      if (langSelect) langSelect.value = 'hi-en';
      const complaintInput = document.getElementById('patChiefComplaint');
      if (complaintInput) complaintInput.value = 'Chest tightness and persistent dry cough for 3 days';
      if (allergiesIn) allergiesIn.value = 'Penicillin (mild rash)';
      if (consentBox) consentBox.checked = true;

      const hp = document.getElementById('histHypertension');
      const db = document.getElementById('histDiabetes');
      if (hp) hp.checked = true;
      if (db) db.checked = true;

      MediTalk.showToast('Sample patient details filled in.', 'info');
    });
  }

  // Simulated ABHA Verification
  if (verifyBtn && abhaInput) {
    verifyBtn.addEventListener('click', () => {
      const val = abhaInput.value.trim();
      const feedback = document.getElementById('abhaVerificationFeedback');
      if (!val) {
        if (feedback) {
          feedback.style.display = 'block';
          feedback.className = 'alert alert-warning py-2 mb-0';
          feedback.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-1"></i> Please enter an ABHA ID first.';
        }
        return;
      }

      verifyBtn.disabled = true;
      verifyBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Verifying...';

      setTimeout(() => {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Verified';
        verifyBtn.className = 'btn btn-outline-success';

        if (feedback) {
          feedback.style.display = 'block';
          feedback.className = 'alert alert-success py-2 mb-0';
          feedback.innerHTML = `
            <div class="d-flex align-items-center gap-2">
              <i class="bi bi-shield-fill-check fs-5 text-success"></i>
              <div>
                <strong>ABDM Sandbox Verified:</strong> ABHA ID active and linked with simulated Health Facility Registry.
              </div>
            </div>
          `;
        }
        MediTalk.showToast('ABHA ID validated via Simulated ABDM Sandbox.', 'success');
      }, 700);
    });
  }

  // Form submission
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    let isValid = true;

    // Validate Name
    if (!nameInput.value.trim()) {
      fieldError(nameInput, document.getElementById('patNameError'), 'Full name is required.');
      isValid = false;
    } else {
      fieldClear(nameInput, document.getElementById('patNameError'));
    }

    // Validate Age
    if (!ageInput.value || Number(ageInput.value) <= 0) {
      fieldError(ageInput, document.getElementById('patAgeError'), 'Please enter a valid age.');
      isValid = false;
    } else {
      fieldClear(ageInput, document.getElementById('patAgeError'));
    }

    // Validate Gender
    if (!genderInput.value) {
      fieldError(genderInput, document.getElementById('patGenderError'), 'Please select gender.');
      isValid = false;
    } else {
      fieldClear(genderInput, document.getElementById('patGenderError'));
    }

    // Validate Phone
    if (!isValidPhone(phoneInput.value)) {
      fieldError(phoneInput, document.getElementById('patPhoneError'), 'Please enter a 10-digit mobile number.');
      isValid = false;
    } else {
      fieldClear(phoneInput, document.getElementById('patPhoneError'));
    }

    // Validate Consent
    const consentErr = document.getElementById('consentError');
    if (!consentBox.checked) {
      if (consentErr) consentErr.style.display = 'block';
      isValid = false;
    } else {
      if (consentErr) consentErr.style.display = 'none';
    }

    // Chief complaint
    const complaintInput = document.getElementById('patChiefComplaint');
    if (complaintInput && !complaintInput.value.trim()) {
      fieldError(complaintInput, document.getElementById('patComplaintError'), 'Please describe your main health problem.');
      isValid = false;
    } else if (complaintInput) {
      fieldClear(complaintInput, document.getElementById('patComplaintError'));
    }

    if (!isValid) {
      MediTalk.showToast('Please fill in the required fields.', 'warning');
      return;
    }

    // Collect conditions
    const conditions = [];
    ['histHypertension', 'histDiabetes', 'histAsthma', 'histHeart'].forEach(id => {
      const el = document.getElementById(id);
      if (el && el.checked) conditions.push(el.value);
    });

    // Save into DataStore
    const patient = MediTalkData.getCurrentPatient();
    patient.demographics = {
      fullName: nameInput.value.trim(),
      age: Number(ageInput.value),
      gender: genderInput.value,
      phone: phoneInput.value.trim(),
      preferredLanguage: langSelect ? langSelect.value : 'en',
      abhaId: 'MT-' + Math.floor(1000 + Math.random() * 9000),
      consentGiven: true,
      consentTimestamp: new Date().toISOString()
    };

    patient.caseTaking = patient.caseTaking || {};
    if (complaintInput && complaintInput.value.trim()) {
      patient.caseTaking.chiefComplaint = complaintInput.value.trim();
    }
    patient.caseTaking.pastMedicalHistory = conditions;
    patient.caseTaking.allergies = allergiesIn && allergiesIn.value.trim() ? allergiesIn.value.trim() : 'No Known Allergies (NKDA)';

    patient.workflowStep = Math.max(patient.workflowStep || 1, 2);
    MediTalkData.saveCurrentPatient(patient);

    MediTalk.showToast('Information saved. Starting Health Assistant.', 'success');
    setTimeout(() => {
      window.location.href = 'chat.html';
    }, 400);
  });
}

// ── STAFF LOGIN FORM ──────────────────────────────────────
function initLoginForm() {
  const loginForm = document.getElementById('loginForm');
  if (!loginForm) return;

  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    MediTalk.showToast('Staff credentials authenticated (Demo Mode). Redirecting...', 'success');
    setTimeout(() => {
      window.location.href = 'doctor-dashboard.html';
    }, 600);
  });
}
