/* =========================================================
   MediKiosk — doctor.js
   Logic for Doctor Dashboard / Clinician Portal (SIH 2026)
   Queue filtering, summary preview, document history, notes, and status
   ========================================================= */

'use strict';

let currentFilter = 'all';
let selectedPatientId = null;

document.addEventListener('DOMContentLoaded', () => {
  initDoctorDashboard();
  setupFilterButtons();
});

function initDoctorDashboard() {
  const patients = MediKioskData.getPatientsList();
  const queueCountEl = document.getElementById('queueCount');
  if (queueCountEl) queueCountEl.textContent = patients.length;

  if (patients.length > 0 && !selectedPatientId) {
    selectedPatientId = patients[0].id;
  }

  renderQueue(patients);
  renderSelectedPatient();
  setupDoctorActions();
}

function setupFilterButtons() {
  document.querySelectorAll('.btn-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter');
      const patients = MediKioskData.getPatientsList();
      renderQueue(patients);
    });
  });
}

function renderQueue(patients) {
  const queueContainer = document.getElementById('patientQueueList');
  if (!queueContainer) return;

  queueContainer.innerHTML = '';

  const filtered = patients.filter(p => {
    const isRedFlag = p.caseTaking?.redFlagStatus === 'HIGH_ALERT' || (p.caseTaking?.redFlagsDetected && p.caseTaking.redFlagsDetected.length > 0);
    const status = p.doctorReview?.status || 'Pending Review';

    if (currentFilter === 'redflag') return isRedFlag;
    if (currentFilter === 'pending') return status === 'Pending Review' || status === 'Under Review';
    if (currentFilter === 'approved') return status === 'Reviewed & Approved';
    return true;
  });

  if (filtered.length === 0) {
    queueContainer.innerHTML = `
      <div class="p-3 text-center text-muted-mt" style="font-size:.85rem;">
        No patients in queue for this filter.
      </div>
    `;
    return;
  }

  filtered.forEach(p => {
    const isRedFlag = p.caseTaking?.redFlagStatus === 'HIGH_ALERT' || (p.caseTaking?.redFlagsDetected && p.caseTaking.redFlagsDetected.length > 0);
    const status = p.doctorReview?.status || 'Pending Review';
    const isSelected = p.id === selectedPatientId;

    let priorityBadge = '';
    if (isRedFlag) {
      priorityBadge = '<span class="badge bg-danger" style="font-size:.68rem;">Urgent / Red-Flag</span>';
    } else if (status === 'Reviewed & Approved') {
      priorityBadge = '<span class="badge bg-success" style="font-size:.68rem;">Approved</span>';
    } else {
      priorityBadge = '<span class="badge bg-warning text-dark" style="font-size:.68rem;">Pending</span>';
    }

    const item = document.createElement('div');
    item.className = `p-3 rounded border text-start position-relative ${isSelected ? 'border-primary bg-blue-light' : 'bg-light'} cursor-pointer`;
    item.style.cursor = 'pointer';
    item.style.transition = 'all .2s ease';

    item.innerHTML = `
      <div class="d-flex justify-content-between align-items-start mb-1">
        <strong style="font-size:.88rem;color:var(--mt-text);">${escapeHtml(p.demographics?.fullName || 'Anonymous Patient')}</strong>
        ${priorityBadge}
      </div>
      <div class="text-muted-mt mb-1" style="font-size:.76rem;">
        ${p.demographics?.age ? p.demographics.age + ' Yrs' : 'Age --'} · ${p.demographics?.gender || '--'} · ID: ${p.id}
      </div>
      <div class="text-truncate fw-500" style="font-size:.78rem;color:#334155;">
        ${escapeHtml(p.caseTaking?.chiefComplaint || 'No chief complaint recorded')}
      </div>
    `;

    item.addEventListener('click', () => {
      selectedPatientId = p.id;
      renderQueue(MediKioskData.getPatientsList());
      renderSelectedPatient();
    });

    queueContainer.appendChild(item);
  });
}

function renderSelectedPatient() {
  const patients = MediKioskData.getPatientsList();
  const patient = patients.find(p => p.id === selectedPatientId) || patients[0];
  if (!patient) return;

  const demo = patient.demographics || {};
  const ct = patient.caseTaking || {};
  const ayush = patient.ayush || {};
  const docs = patient.documents || [];
  const review = patient.doctorReview || {};

  setText('dpFullName', demo.fullName || 'Unknown Patient');
  setText('dpAgeGender', `${demo.age ? demo.age + ' Yrs' : 'Age --'} / ${demo.gender || '--'}`);
  setText('dpId', patient.id || 'MK-0000');
  setText('dpAbha', demo.abhaId || 'Unlinked');
  setText('dpPhone', demo.phone || 'No phone recorded');

  // Priority Badge
  const badgeEl = document.getElementById('dpPriorityBadge');
  const isRedFlag = ct.redFlagStatus === 'HIGH_ALERT' || (ct.redFlagsDetected && ct.redFlagsDetected.length > 0);
  if (badgeEl) {
    if (isRedFlag) {
      badgeEl.className = 'badge bg-danger';
      badgeEl.textContent = 'High Priority (Red Flag)';
    } else if (review.status === 'Reviewed & Approved') {
      badgeEl.className = 'badge bg-success';
      badgeEl.textContent = 'Approved & Signed Off';
    } else {
      badgeEl.className = 'badge bg-warning text-dark';
      badgeEl.textContent = 'Normal Triage Priority';
    }
  }

  // Red Flag Alert Box
  const rfBox = document.getElementById('dpRedFlagAlert');
  if (rfBox) {
    if (isRedFlag) {
      const flags = ct.redFlagsDetected || ['High severity cardiac/respiratory warning'];
      rfBox.innerHTML = `
        <div class="red-flag-banner py-2 px-3 mb-3" style="font-size:.85rem;">
          <i class="bi bi-exclamation-triangle-fill fs-5 mt-1"></i>
          <div>
            <strong>URGENT RED-FLAG CLINICAL WARNING:</strong>
            <ul class="mb-0 ps-3">
              ${flags.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
            </ul>
          </div>
        </div>
      `;
    } else {
      rfBox.innerHTML = '';
    }
  }

  // Missing Info Alert
  const miBox = document.getElementById('dpMissingInfo');
  if (miBox) {
    const missing = MediKioskData.detectMissingInformation(patient);
    if (missing.length > 0) {
      miBox.innerHTML = `
        <div class="missing-info-box py-2 px-3 mb-3" style="font-size:.82rem;">
          <strong><i class="bi bi-info-circle-fill me-1"></i> Missing Clinical Parameters:</strong>
          ${missing.join(' · ')}
        </div>
      `;
    } else {
      miBox.innerHTML = '';
    }
  }

  // Chief Complaint & Symptoms
  setText('dpChiefComplaint', ct.chiefComplaint || 'No chief complaint articulated.');
  setText('dpDuration', ct.durationValue ? `${ct.durationValue} ${ct.durationUnit || 'days'}` : 'Unspecified');
  setText('dpSeverity', `${ct.severity || 1} / 10`);

  const tagsContainer = document.getElementById('dpSymptomsTags');
  if (tagsContainer) {
    tagsContainer.innerHTML = '';
    (ct.symptoms || []).forEach(s => {
      const sp = document.createElement('span');
      sp.className = 'pill pill-blue';
      sp.style.fontSize = '.72rem';
      sp.textContent = s;
      tagsContainer.appendChild(sp);
    });
  }

  // History, Meds, Allergies
  setText('dpHistory', (ct.pastMedicalHistory || []).join(', ') || 'None recorded');
  setText('dpMeds', ct.currentMedications || 'None reported');
  setText('dpAllergies', ct.allergies || 'Not recorded');

  // Documents
  const docsContainer = document.getElementById('dpDocumentsList');
  if (docsContainer) {
    docsContainer.innerHTML = '';
    if (docs.length === 0) {
      docsContainer.innerHTML = `
        <div class="col-12">
          <div class="p-2 border rounded bg-light text-muted-mt" style="font-size:.8rem;">
            No documents attached for this patient intake.
          </div>
        </div>
      `;
    } else {
      docs.forEach(d => {
        const ocr = d.simulatedOcr || {};
        const col = document.createElement('div');
        col.className = 'col-md-6';
        col.innerHTML = `
          <div class="p-2 border rounded bg-light h-100" style="font-size:.8rem;">
            <div class="d-flex justify-content-between">
              <strong>${escapeHtml(d.title || d.fileName)}</strong>
              <span class="badge bg-secondary" style="font-size:.65rem;">${escapeHtml(d.category)}</span>
            </div>
            <div class="text-muted-mt" style="font-size:.74rem;">Date: ${ocr.date || 'N/A'} · ${escapeHtml(ocr.doctorName || ocr.facilityName || '')}</div>
            <div class="mt-1"><strong>Extracted:</strong> ${escapeHtml(ocr.extractedDiagnosis || ocr.findings || 'No text extracted')}</div>
            ${ocr.extractedMedications ? `<div class="text-muted-mt"><strong>Meds:</strong> ${escapeHtml(ocr.extractedMedications)}</div>` : ''}
          </div>
        `;
        docsContainer.appendChild(col);
      });
    }
  }

  // AYUSH
  const ayushWrap = document.getElementById('dpAyushWrap');
  const ayushGrid = document.getElementById('dpAyushGrid');
  if (ayushWrap && ayushGrid) {
    if (ayush.enabled && (ayush.prakriti || ayush.vikriti)) {
      ayushWrap.style.display = 'block';
      ayushGrid.innerHTML = `
        <div class="col-sm-4"><strong>Prakriti:</strong> ${escapeHtml(ayush.prakriti || '--')}</div>
        <div class="col-sm-4"><strong>Vikriti:</strong> ${escapeHtml(ayush.vikriti || '--')}</div>
        <div class="col-sm-4"><strong>Agni:</strong> ${escapeHtml(ayush.aharaShakti || '--')}</div>
        <div class="col-sm-4"><strong>Sara:</strong> ${escapeHtml(ayush.sara || '--')}</div>
        <div class="col-sm-4"><strong>Satva:</strong> ${escapeHtml(ayush.satva || '--')}</div>
        <div class="col-sm-4"><strong>Vyayama:</strong> ${escapeHtml(ayush.vyayamaShakti || '--')}</div>
      `;
    } else {
      ayushWrap.style.display = 'none';
    }
  }

  // Doctor Review Inputs
  const statusSelect = document.getElementById('dpReviewStatusSelect');
  const impressionInput = document.getElementById('dpProvisionalImpression');
  const notesInput = document.getElementById('dpDoctorNotes');

  if (statusSelect) statusSelect.value = review.status || 'Pending Review';
  if (impressionInput) impressionInput.value = review.provisionalImpression || '';
  if (notesInput) notesInput.value = review.notes || '';
}

function setupDoctorActions() {
  const saveBtn = document.getElementById('dpSaveReviewBtn');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      const patients = MediKioskData.getPatientsList();
      const patient = patients.find(p => p.id === selectedPatientId);
      if (!patient) return;

      const statusSelect = document.getElementById('dpReviewStatusSelect');
      const impressionInput = document.getElementById('dpProvisionalImpression');
      const notesInput = document.getElementById('dpDoctorNotes');

      patient.doctorReview = patient.doctorReview || {};
      if (statusSelect) patient.doctorReview.status = statusSelect.value;
      if (impressionInput) patient.doctorReview.provisionalImpression = impressionInput.value.trim();
      if (notesInput) patient.doctorReview.notes = notesInput.value.trim();
      patient.doctorReview.reviewedAt = new Date().toISOString();
      patient.doctorReview.reviewedBy = 'Dr. Sanjay K. Mehta, MBBS, MD';

      MediKioskData.savePatientsList(patients);

      // If active current patient matches, sync it as well
      const curr = MediKioskData.getCurrentPatient();
      if (curr && curr.id === patient.id) {
        MediKioskData.saveCurrentPatient(patient);
      }

      renderQueue(patients);
      renderSelectedPatient();
      MediTalk.showToast('Clinical review and impression saved successfully.', 'success');
    });
  }

  // FHIR Modal
  const fhirBtn = document.getElementById('docFhirBtn');
  if (fhirBtn) {
    fhirBtn.addEventListener('click', () => {
      const patients = MediKioskData.getPatientsList();
      const patient = patients.find(p => p.id === selectedPatientId);
      if (!patient) return;
      const bundle = MediKioskData.generateFHIRBundle(patient);
      const codeEl = document.getElementById('docFhirCode');
      if (codeEl) codeEl.textContent = JSON.stringify(bundle, null, 2);
      const modalEl = document.getElementById('docFhirModal');
      if (modalEl && window.bootstrap) {
        new bootstrap.Modal(modalEl).show();
      }
    });
  }

  // Print
  const printBtn = document.getElementById('docPrintBtn');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      window.location.href = 'summary.html';
    });
  }
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
