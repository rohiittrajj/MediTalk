/* =========================================================
   MediKiosk — image-analysis.js
   Medical Document Scanning & Simulated OCR (Scan Step)
   Drag-and-drop, validation, simulated extraction, editable fields,
   and integration with the central patient record data store.
   ========================================================= */

'use strict';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
const MAX_SIZE_MB   = 10;

// DOM Elements
const dropZone        = document.getElementById('dropZone');
const fileInput       = document.getElementById('fileInput');
const browseBtn       = document.getElementById('browseBtn');
const previewWrap     = document.getElementById('previewSection');
const previewImg      = document.getElementById('previewImg');
const pdfIcon         = document.getElementById('pdfIcon');
const fileNameEl      = document.getElementById('previewFileName');
const fileSizeEl      = document.getElementById('previewFileSize');
const removeBtn       = document.getElementById('removeFileBtn');
const analyzeBtn      = document.getElementById('analyzeBtn');
const errorEl         = document.getElementById('uploadError');
const errorText       = document.getElementById('uploadErrorText');

const categorySelect  = document.getElementById('docCategorySelect');
const docTitleInput   = document.getElementById('ocrDocTitle');
const docDateInput    = document.getElementById('ocrDate');
const docFacilityInput= document.getElementById('ocrFacility');
const docFindingsInput= document.getElementById('ocrFindings');
const docMedsInput    = document.getElementById('ocrMeds');
const docNotesInput   = document.getElementById('ocrNotes');
const saveDocBtn      = document.getElementById('saveDocToRecordBtn');
const attachedListEl  = document.getElementById('attachedDocsList');
const attachedCountEl = document.getElementById('attachedDocsCount');
const sampleRxBtn     = document.getElementById('loadSampleRxBtn');
const sampleLabBtn    = document.getElementById('loadSampleLabBtn');

let currentFile = null;

document.addEventListener('DOMContentLoaded', () => {
  initDocumentScanner();
  setupSampleButtons();
  renderAttachedDocuments();
});

function initDocumentScanner() {
  const patient = MediKioskData.getCurrentPatient();
  const nameEl = document.getElementById('scanPatNameDisplay');
  if (nameEl && patient?.demographics?.fullName) {
    nameEl.textContent = patient.demographics.fullName;
  }

  // File browse
  if (browseBtn && fileInput) {
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', e => {
      if (e.target.files && e.target.files[0]) handleFile(e.target.files[0]);
    });
  }

  // Drag and drop
  if (dropZone) {
    dropZone.addEventListener('click', () => fileInput && fileInput.click());
    ['dragenter', 'dragover'].forEach(ev => {
      dropZone.addEventListener(ev, e => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
      });
    });
    ['dragleave', 'drop'].forEach(ev => {
      dropZone.addEventListener(ev, e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
      });
    });
    dropZone.addEventListener('drop', e => {
      if (e.dataTransfer?.files?.length) handleFile(e.dataTransfer.files[0]);
    });
  }

  // Remove preview
  if (removeBtn) {
    removeBtn.addEventListener('click', () => removeFile());
  }

  // Analyze Button (Trigger Simulated OCR)
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', () => runSimulatedOCR());
  }

  // Save to Record Button
  if (saveDocBtn) {
    saveDocBtn.addEventListener('click', () => saveCurrentDocToRecord());
  }
}

function handleFile(file) {
  if (!file) return;
  hideError();

  if (!ALLOWED_TYPES.includes(file.type)) {
    showError('Unsupported file type. Please upload JPG, PNG, WEBP, or PDF files.');
    return;
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    showError(`File size exceeds ${MAX_SIZE_MB}MB limit.`);
    return;
  }

  currentFile = file;
  if (fileNameEl) fileNameEl.textContent = file.name;
  if (fileSizeEl) fileSizeEl.textContent = (file.size / 1024).toFixed(1) + ' KB';

  const isPdf = file.type === 'application/pdf';
  if (previewImg) previewImg.style.display = isPdf ? 'none' : 'block';
  if (pdfIcon) pdfIcon.style.display = isPdf ? 'flex' : 'none';

  if (!isPdf) {
    const reader = new FileReader();
    reader.onload = e => { if (previewImg) previewImg.src = e.target.result; };
    reader.readAsDataURL(file);
  }

  if (previewWrap) previewWrap.style.display = 'block';

  // Automatically adapt title
  if (docTitleInput) {
    docTitleInput.value = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
  }

  runSimulatedOCR();
}

function removeFile() {
  currentFile = null;
  if (fileInput) fileInput.value = '';
  if (previewWrap) previewWrap.style.display = 'none';
  if (previewImg) previewImg.src = '';
  hideError();
}

function showError(msg) {
  if (errorEl) {
    errorEl.style.display = 'flex';
    if (errorText) errorText.textContent = msg;
  }
}
function hideError() {
  if (errorEl) errorEl.style.display = 'none';
}

function runSimulatedOCR() {
  const category = categorySelect ? categorySelect.value : 'Prescription';

  if (analyzeBtn) {
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Extracting OCR data...';
  }

  setTimeout(() => {
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> OCR Extraction Complete';
    }

    if (category === 'Laboratory Report') {
      if (docTitleInput) docTitleInput.value = 'Complete Blood Count & Metabolic Profile';
      if (docFacilityInput) docFacilityInput.value = 'Apex Path Labs — Dr. Priya Sen (MD Pathologist)';
      if (docDateInput) docDateInput.value = '2026-10-18';
      if (docFindingsInput) docFindingsInput.value = 'Hemoglobin: 12.8 g/dL (Normal), Total Leukocyte Count: 9,200 /uL, Fasting Blood Sugar: 122 mg/dL (Borderline elevated).';
      if (docMedsInput) docMedsInput.value = 'N/A (Diagnostic Pathology Investigation)';
      if (docNotesInput) docNotesInput.value = 'Repeat FBS and HbA1c in 3 months. No acute leukocytosis.';
    } else if (category === 'Discharge Summary') {
      if (docTitleInput) docTitleInput.value = 'Hospital Admission Discharge Summary';
      if (docFacilityInput) docFacilityInput.value = 'City Care Hospital — Dept of Pulmonology';
      if (docDateInput) docDateInput.value = '2026-08-20';
      if (docFindingsInput) docFindingsInput.value = 'Discharged in stable condition following 48h observation for acute viral tracheobronchitis.';
      if (docMedsInput) docMedsInput.value = 'Tab Azithromycin 500mg OD x 3 days, Tab Montelukast 10mg HS';
      if (docNotesInput) docNotesInput.value = 'Chest X-ray clear prior to discharge. Advised steam inhalation.';
    } else {
      if (docTitleInput) docTitleInput.value = 'Previous Clinic Prescription';
      if (docFacilityInput) docFacilityInput.value = 'Metro Health Clinic — Dr. A. K. Sharma (MD Internal Med)';
      if (docDateInput) docDateInput.value = '2026-09-15';
      if (docFindingsInput) docFindingsInput.value = 'Essential Hypertension - Stage 1. Advised sodium restriction and regular BP monitoring.';
      if (docMedsInput) docMedsInput.value = 'Tab Telmisartan 40mg OD mornings x 30 days';
      if (docNotesInput) docNotesInput.value = 'Patient advised to repeat ECG if chest tightness recurs.';
    }

    MediTalk.showToast('Simulated OCR extraction complete. Verify values before saving.', 'info');
  }, 500);
}

function setupSampleButtons() {
  if (sampleRxBtn) {
    sampleRxBtn.addEventListener('click', () => {
      if (categorySelect) categorySelect.value = 'Prescription';
      if (previewFileName) previewFileName.textContent = 'Rx_DrSharma_Clinic.pdf';
      if (previewFileSize) previewFileSize.textContent = '145.2 KB';
      if (previewWrap) previewWrap.style.display = 'block';
      if (previewImg) previewImg.style.display = 'none';
      if (pdfIcon) pdfIcon.style.display = 'flex';
      runSimulatedOCR();
    });
  }

  if (sampleLabBtn) {
    sampleLabBtn.addEventListener('click', () => {
      if (categorySelect) categorySelect.value = 'Laboratory Report';
      if (previewFileName) previewFileName.textContent = 'CBC_Blood_Pathology.png';
      if (previewFileSize) previewFileSize.textContent = '320.5 KB';
      if (previewWrap) previewWrap.style.display = 'block';
      if (previewImg) {
        previewImg.style.display = 'block';
        previewImg.src = 'assets/icon-192.png';
      }
      if (pdfIcon) pdfIcon.style.display = 'none';
      runSimulatedOCR();
    });
  }
}

function saveCurrentDocToRecord() {
  const patient = MediKioskData.getCurrentPatient();
  if (!patient) return;

  const doc = {
    id: 'doc-' + Date.now().toString().slice(-4),
    title: docTitleInput ? docTitleInput.value.trim() : 'Medical Document',
    category: categorySelect ? categorySelect.value : 'Prescription',
    fileName: currentFile ? currentFile.name : (docTitleInput ? docTitleInput.value + '.pdf' : 'Document.pdf'),
    uploadDate: new Date().toISOString().split('T')[0],
    simulatedOcr: {
      facilityName: docFacilityInput ? docFacilityInput.value.trim() : '',
      doctorName: docFacilityInput ? docFacilityInput.value.trim() : '',
      date: docDateInput ? docDateInput.value : '',
      extractedDiagnosis: docFindingsInput ? docFindingsInput.value.trim() : '',
      extractedMedications: docMedsInput ? docMedsInput.value.trim() : '',
      extractedNotes: docNotesInput ? docNotesInput.value.trim() : ''
    }
  };

  patient.documents = patient.documents || [];
  patient.documents.unshift(doc);
  patient.workflowStep = Math.max(patient.workflowStep || 1, 3);
  MediKioskData.saveCurrentPatient(patient);

  renderAttachedDocuments();
  MediTalk.showToast('Document saved to patient record and synced with summary.', 'success');
}

function renderAttachedDocuments() {
  if (!attachedListEl) return;
  const patient = MediKioskData.getCurrentPatient();
  const docs = patient?.documents || [];

  if (attachedCountEl) attachedCountEl.textContent = docs.length;

  if (docs.length === 0) {
    attachedListEl.innerHTML = `
      <div class="p-2 border rounded bg-light text-muted-mt text-center" style="font-size:.78rem;">
        No documents currently attached to this patient session.
      </div>
    `;
    return;
  }

  attachedListEl.innerHTML = '';
  docs.forEach((d, idx) => {
    const item = document.createElement('div');
    item.className = 'p-2 border rounded bg-light d-flex justify-content-between align-items-center';
    item.innerHTML = `
      <div class="text-truncate me-2" style="font-size:.8rem;">
        <i class="bi bi-file-earmark-medical text-primary me-1"></i>
        <strong>${escapeHtml(d.title || d.fileName)}</strong>
        <span class="badge bg-secondary ms-1" style="font-size:.65rem;">${escapeHtml(d.category)}</span>
      </div>
      <button type="button" class="btn btn-sm btn-outline-danger p-0 px-2" title="Delete document" data-idx="${idx}">
        <i class="bi bi-trash"></i>
      </button>
    `;

    item.querySelector('button').addEventListener('click', (e) => {
      e.stopPropagation();
      docs.splice(idx, 1);
      patient.documents = docs;
      MediKioskData.saveCurrentPatient(patient);
      renderAttachedDocuments();
      MediTalk.showToast('Document removed from record.', 'info');
    });

    attachedListEl.appendChild(item);
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
