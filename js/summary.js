/* =========================================================
   MediKiosk — summary.js
   Logic for Medical Summary Generator (SIH 2026)
   Editable clinical sheet, red-flag alert, missing info detection,
   print/PDF export, and ABDM/FHIR R4 bundle integration.
   ========================================================= */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  renderSummary();
  setupEventListeners();
});

// Re-render when language changes
window.addEventListener('medikiosk:langChanged', () => {
  renderSummary();
});

function renderSummary() {
  const patient = MediKioskData.getCurrentPatient();
  if (!patient) return;

  const demo = patient.demographics || {};
  const ct = patient.caseTaking || {};
  const ayush = patient.ayush || {};
  const docs = patient.documents || [];
  const review = patient.doctorReview || {};

  // Header
  const idEl = document.getElementById('sumPatientId');
  if (idEl) idEl.textContent = 'ID: ' + (patient.id || 'MK-2026-0001');

  const tsEl = document.getElementById('sumTimestamp');
  if (tsEl) {
    const d = patient.registeredAt ? new Date(patient.registeredAt) : new Date();
    tsEl.textContent = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // 1. Demographics
  setText('sumFullName', demo.fullName || 'Not recorded');
  setText('sumAgeGender', `${demo.age ? demo.age + ' Yrs' : 'Age Unspecified'} / ${demo.gender || 'Unspecified'}`);
  setText('sumPhone', demo.phone || 'Not recorded');
  setText('sumAbhaId', demo.abhaId || 'Not Linked (ABDM)');
  
  const abhaStatusEl = document.getElementById('sumAbhaStatus');
  if (abhaStatusEl) {
    if (demo.abhaId) {
      abhaStatusEl.textContent = demo.abhaStatus || 'Simulated ABDM Verified';
      abhaStatusEl.className = 'pill pill-teal ms-1';
    } else {
      abhaStatusEl.textContent = 'Unlinked';
      abhaStatusEl.className = 'pill pill-amber ms-1';
    }
  }

  const langMap = { en: 'English', hi: 'Hindi (हिंदी)', 'hi-en': 'Hinglish' };
  setText('sumLanguage', langMap[demo.preferredLanguage] || demo.preferredLanguage || 'English');

  const emergText = (demo.emergencyContactName ? demo.emergencyContactName + ' ' : '') + 
                    (demo.emergencyContactPhone ? `(${demo.emergencyContactPhone})` : 'Not provided');
  setText('sumEmergencyContact', emergText);

  const consentEl = document.getElementById('sumConsentStatus');
  if (consentEl) {
    if (demo.consentGiven) {
      consentEl.textContent = 'Recorded on Intake';
      consentEl.className = 'pill pill-green';
    } else {
      consentEl.textContent = 'Consent Pending';
      consentEl.className = 'pill pill-amber';
    }
  }

  // 2. Chief Complaint & Timeline
  setText('sumChiefComplaint', ct.chiefComplaint || 'No chief complaint recorded yet.');
  setText('sumDuration', ct.durationValue ? `${ct.durationValue} ${ct.durationUnit || 'days'}` : 'Unspecified');

  const severityBadge = document.getElementById('sumSeverityBadge');
  const severityText = document.getElementById('sumSeverityText');
  const sev = Number(ct.severity) || 1;
  if (severityBadge) {
    severityBadge.textContent = `${sev} / 10`;
    if (sev >= 8) {
      severityBadge.className = 'badge bg-danger fs-6';
      if (severityText) severityText.textContent = 'Severe / Critical';
    } else if (sev >= 5) {
      severityBadge.className = 'badge bg-warning text-dark fs-6';
      if (severityText) severityText.textContent = 'Moderate';
    } else {
      severityBadge.className = 'badge bg-success fs-6';
      if (severityText) severityText.textContent = 'Mild';
    }
  }

  const notesWrap = document.getElementById('sumSymptomNotesWrap');
  if (notesWrap) {
    if (ct.symptomNotes) {
      notesWrap.style.display = 'block';
      setText('sumSymptomNotes', `"${ct.symptomNotes}"`);
    } else {
      notesWrap.style.display = 'none';
    }
  }

  // 3. Associated Symptoms
  const symptomsContainer = document.getElementById('sumSymptomsList');
  if (symptomsContainer) {
    symptomsContainer.innerHTML = '';
    const syms = ct.symptoms || [];
    if (syms.length === 0) {
      symptomsContainer.innerHTML = '<span class="text-muted-mt" style="font-size:.85rem;">No additional specific symptoms checked during intake.</span>';
    } else {
      syms.forEach(s => {
        const span = document.createElement('span');
        const isRedFlag = s.toLowerCase().includes('chest') || s.toLowerCase().includes('breath') || s.toLowerCase().includes('bleed');
        span.className = isRedFlag ? 'red-flag-pill' : 'pill pill-blue';
        span.innerHTML = `<i class="bi ${isRedFlag ? 'bi-exclamation-octagon-fill' : 'bi-check2'}"></i> ${escapeHtml(s)}`;
        symptomsContainer.appendChild(span);
      });
    }
  }

  // 4. History, Medications, Allergies
  const histList = ct.pastMedicalHistory || [];
  setText('sumPastHistory', histList.length > 0 ? histList.join(', ') : 'None reported / Incomplete');
  setText('sumPastHistoryNotes', ct.pastHistoryNotes ? `Notes: ${ct.pastHistoryNotes}` : '');
  setText('sumCurrentMeds', ct.currentMedications || 'No current medications reported');
  
  const allergyEl = document.getElementById('sumAllergies');
  if (allergyEl) {
    if (ct.allergies) {
      allergyEl.textContent = ct.allergies;
      allergyEl.style.color = '#92400e';
    } else {
      allergyEl.textContent = 'Not specified (Pending clinician confirmation)';
      allergyEl.style.color = '#64748b';
    }
  }

  // 5. Uploaded Documents
  const docsContainer = document.getElementById('sumDocumentsList');
  if (docsContainer) {
    docsContainer.innerHTML = '';
    if (docs.length === 0) {
      docsContainer.innerHTML = `
        <div class="p-3 border rounded-3 bg-light text-muted-mt" style="font-size:.86rem;">
          <i class="bi bi-folder2-open me-1"></i> No prior medical prescriptions or laboratory investigation documents uploaded.
          <a href="image-analysis.html" class="ms-2 fw-600 text-decoration-underline no-print">Upload Document Now</a>
        </div>
      `;
    } else {
      docs.forEach(doc => {
        const ocr = doc.simulatedOcr || {};
        const card = document.createElement('div');
        card.className = 'card-mt p-3 mb-2 bg-white border';
        card.innerHTML = `
          <div class="d-flex flex-wrap justify-content-between align-items-center mb-2">
            <div>
              <strong style="font-size:.92rem;color:var(--mt-blue-dark);">${escapeHtml(doc.title || doc.fileName || 'Attached Document')}</strong>
              <span class="badge bg-secondary ms-2" style="font-size:.72rem;">${escapeHtml(doc.category || 'General Document')}</span>
            </div>
            <span class="pill pill-teal" style="font-size:.72rem;"><i class="bi bi-clock"></i> Uploaded: ${doc.uploadDate || 'Recent'}</span>
          </div>
          <div class="p-2 rounded bg-light border" style="font-size:.82rem;">
            <div class="row g-2">
              <div class="col-sm-6"><strong>Facility/Doctor:</strong> ${escapeHtml(ocr.doctorName || ocr.facilityName || 'N/A')}</div>
              <div class="col-sm-6"><strong>Doc Date:</strong> ${escapeHtml(ocr.date || 'N/A')}</div>
              <div class="col-12"><strong>Extracted Findings / Diagnosis:</strong> ${escapeHtml(ocr.extractedDiagnosis || ocr.findings || 'No text extracted')}</div>
              ${ocr.extractedMedications ? `<div class="col-12"><strong>Extracted Meds:</strong> ${escapeHtml(ocr.extractedMedications)}</div>` : ''}
              ${ocr.extractedNotes ? `<div class="col-12 text-muted-mt"><strong>Notes:</strong> ${escapeHtml(ocr.extractedNotes)}</div>` : ''}
            </div>
          </div>
        `;
        docsContainer.appendChild(card);
      });
    }
  }

  // 6. AYUSH Dashavidha Pariksha
  const ayushWrap = document.getElementById('ayushSectionWrap');
  const ayushGrid = document.getElementById('sumAyushGrid');
  if (ayushWrap && ayushGrid) {
    if (ayush.enabled && (ayush.prakriti || ayush.vikriti)) {
      ayushWrap.style.display = 'block';
      const categories = [
        { name: '1. Prakriti (Constitution)', val: ayush.prakriti, desc: 'Dominant Dosha type' },
        { name: '2. Vikriti (Imbalance)', val: ayush.vikriti, desc: 'Current clinical pathogenesis' },
        { name: '3. Sara (Tissue Quality)', val: ayush.sara, desc: 'Dhatu excellence' },
        { name: '4. Samhanana (Body Build)', val: ayush.samhanana, desc: 'Compactness & structure' },
        { name: '5. Pramana (Proportions)', val: ayush.pramana, desc: 'Anthropometry & BMI' },
        { name: '6. Satmya (Habituation)', val: ayush.satmya, desc: 'Dietary & physical adaptability' },
        { name: '7. Satva (Mental Strength)', val: ayush.satva, desc: 'Psychological resilience' },
        { name: '8. Ahara Shakti (Digestion)', val: ayush.aharaShakti, desc: 'Appetite & metabolic power' },
        { name: '9. Vyayama Shakti (Endurance)', val: ayush.vyayamaShakti, desc: 'Physical capacity' },
        { name: '10. Vaya (Life Stage)', val: ayush.vaya, desc: 'Age category assessment' }
      ];

      ayushGrid.innerHTML = categories.map(c => `
        <div class="col-sm-6 col-md-4">
          <div class="p-2 border rounded bg-light h-100">
            <span class="d-block fw-700 text-teal-dark" style="font-size:.78rem;color:var(--mt-teal-dark);">${c.name}</span>
            <div style="font-size:.85rem;font-weight:600;color:var(--mt-text);">${escapeHtml(c.val || 'Not assessed')}</div>
            <span class="text-muted-mt d-block" style="font-size:.72rem;">${c.desc}</span>
          </div>
        </div>
      `).join('');

      setText('sumAyushNotes', ayush.notes || 'No supplementary Ayurvedic notes recorded.');
    } else {
      ayushWrap.style.display = 'block';
      ayushGrid.innerHTML = `
        <div class="col-12">
          <div class="p-3 border rounded bg-light text-muted-mt d-flex justify-content-between align-items-center">
            <span><i class="bi bi-info-circle me-1"></i> AYUSH Dashavidha Pariksha assessment not yet evaluated for this session.</span>
            <a href="ayush.html" class="btn btn-sm btn-outline-success no-print"><i class="bi bi-flower1 me-1"></i> Open AYUSH Module</a>
          </div>
        </div>
      `;
      const notesEl = document.getElementById('sumAyushNotesWrap');
      if (notesEl) notesEl.style.display = 'none';
    }
  }

  // 7. Doctor Review Section
  const statusSelect = document.getElementById('doctorStatusSelect');
  const statusBadge = document.getElementById('doctorStatusBadge');
  const notesInput = document.getElementById('doctorNotesInput');
  const doctorNameDisplay = document.getElementById('doctorNameDisplay');

  if (statusSelect) statusSelect.value = review.status || 'Pending Review';
  if (notesInput) notesInput.value = review.notes || '';
  if (doctorNameDisplay && review.doctorName) doctorNameDisplay.textContent = review.doctorName;

  if (statusBadge) {
    const s = review.status || 'Pending Review';
    statusBadge.textContent = s;
    if (s === 'Reviewed & Approved') {
      statusBadge.className = 'pill pill-green';
    } else if (s === 'Under Review') {
      statusBadge.className = 'pill pill-blue';
    } else {
      statusBadge.className = 'pill pill-amber';
    }
  }

  // 8. Red-Flag Check
  renderRedFlags(patient);

  // 9. Missing Information Check
  renderMissingInfo(patient);
}

function renderRedFlags(patient) {
  const container = document.getElementById('redFlagAlertContainer');
  if (!container) return;

  const ct = patient.caseTaking || {};
  const redFlagAnalysis = MediKioskData.detectRedFlags(
    ct.chiefComplaint + ' ' + (ct.symptomNotes || ''),
    ct.symptoms || [],
    ct.severity || 5
  );

  const flags = Array.from(new Set([...(ct.redFlagsDetected || []), ...redFlagAnalysis.redFlags]));

  if (flags.length > 0) {
    container.innerHTML = `
      <div class="red-flag-banner" role="alert">
        <i class="bi bi-exclamation-triangle-fill" style="font-size:1.8rem;flex-shrink:0;"></i>
        <div>
          <h5 class="fw-800 mb-1" style="font-size:1rem;color:#9f1239;">
            <i class="bi bi-radioactive me-1"></i> POTENTIAL RED-FLAG EMERGENCY SYMPTOMS IDENTIFIED
          </h5>
          <p class="mb-2" style="font-size:.875rem;">
            The automated triage engine detected critical indicators requiring priority clinician evaluation:
          </p>
          <ul class="mb-2 ps-3" style="font-size:.85rem;">
            ${flags.map(f => `<li><strong>${escapeHtml(f)}</strong></li>`).join('')}
          </ul>
          <span class="badge bg-danger">Priority 1 Triage Tag</span>
          <span class="text-muted-mt ms-2" style="font-size:.78rem;color:#881337 !important;">
            Attending emergency staff alerted via kiosk monitoring queue.
          </span>
        </div>
      </div>
    `;
  } else {
    container.innerHTML = '';
  }
}

function renderMissingInfo(patient) {
  const container = document.getElementById('missingInfoContainer');
  if (!container) return;

  const missing = MediKioskData.detectMissingInformation(patient);
  if (missing.length > 0) {
    container.innerHTML = `
      <div class="missing-info-box no-print" role="region" aria-label="Missing patient data checklist">
        <div class="d-flex align-items-center justify-content-between mb-1">
          <strong class="d-flex align-items-center gap-1">
            <i class="bi bi-patch-question-fill text-warning"></i> Missing Patient Clinical Information (${missing.length})
          </strong>
          <span style="font-size:.75rem;font-weight:700;">Please verify before finalizing</span>
        </div>
        <p class="mb-1" style="font-size:.82rem;">The following fields were left blank or unrecorded during intake:</p>
        <ul class="mb-0 ps-3" style="font-size:.82rem;">
          ${missing.map(m => `<li>${escapeHtml(m)}</li>`).join('')}
        </ul>
      </div>
    `;
  } else {
    container.innerHTML = '';
  }
}

function setupEventListeners() {
  // Save Draft
  const saveBtn = document.getElementById('saveDraftBtn');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      saveSummaryChanges(false);
      MediTalk.showToast('Medical Summary draft saved to local storage.', 'success');
    });
  }

  // Print
  const printBtn = document.getElementById('printBtn');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      saveSummaryChanges(false);
      window.print();
    });
  }

  // PDF Export (using window.print())
  const pdfBtn = document.getElementById('pdfBtn');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', () => {
      saveSummaryChanges(false);
      MediTalk.showToast('Select "Save as PDF" in your print dialog destination.', 'info', 4000);
      setTimeout(() => {
        window.print();
      }, 500);
    });
  }

  // Edit Data button
  const editBtn = document.getElementById('editDataBtn');
  if (editBtn) {
    editBtn.addEventListener('click', () => {
      window.location.href = 'chat.html';
    });
  }

  // Doctor status change live
  const statusSelect = document.getElementById('doctorStatusSelect');
  if (statusSelect) {
    statusSelect.addEventListener('change', () => {
      saveSummaryChanges(false);
      renderSummary();
    });
  }

  // FHIR Modal button
  const fhirBtn = document.getElementById('fhirBtn');
  if (fhirBtn) {
    fhirBtn.addEventListener('click', () => {
      const patient = MediKioskData.getCurrentPatient();
      const bundle = MediKioskData.generateFHIRBundle(patient);
      const codeEl = document.getElementById('fhirPayloadCode');
      if (codeEl) {
        codeEl.textContent = JSON.stringify(bundle, null, 2);
      }
      const modalEl = document.getElementById('fhirModal');
      if (modalEl && window.bootstrap) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
      }
    });
  }
}

function saveSummaryChanges(silent = true) {
  const patient = MediKioskData.getCurrentPatient();
  if (!patient) return;

  const notesInput = document.getElementById('doctorNotesInput');
  const statusSelect = document.getElementById('doctorStatusSelect');

  if (notesInput) {
    patient.doctorReview.notes = notesInput.value.trim();
  }
  if (statusSelect) {
    patient.doctorReview.status = statusSelect.value;
    if (statusSelect.value === 'Reviewed & Approved' && !patient.doctorReview.reviewedAt) {
      patient.doctorReview.reviewedAt = new Date().toISOString();
    }
  }

  MediKioskData.saveCurrentPatient(patient);
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
