/* =========================================================
   MediKiosk — ayush.js
   Logic for Dashavidha Pariksha (10 categories)
   Saves to localStorage and syncs with Medical Summary
   ========================================================= */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  loadAyushData();
  setupAyushForm();
});

function loadAyushData() {
  const patient = MediKioskData.getCurrentPatient();
  if (!patient) return;

  const ayush = patient.ayush || {};

  const switchEl = document.getElementById('enableAyushSwitch');
  if (switchEl) switchEl.checked = ayush.enabled !== false;

  setSelectVal('ayushPrakriti', ayush.prakriti);
  setSelectVal('ayushVikriti', ayush.vikriti);
  setSelectVal('ayushSara', ayush.sara);
  setSelectVal('ayushSamhanana', ayush.samhanana);
  setSelectVal('ayushPramana', ayush.pramana);
  setSelectVal('ayushSatmya', ayush.satmya);
  setSelectVal('ayushSatva', ayush.satva);
  setSelectVal('ayushAharaShakti', ayush.aharaShakti);
  setSelectVal('ayushVyayamaShakti', ayush.vyayamaShakti);
  setSelectVal('ayushVaya', ayush.vaya);

  const notesEl = document.getElementById('ayushNotes');
  if (notesEl && ayush.notes) notesEl.value = ayush.notes;
}

function setupAyushForm() {
  const form = document.getElementById('ayushForm');
  const saveBtn = document.getElementById('saveAyushBtn');

  if (saveBtn) {
    saveBtn.addEventListener('click', (e) => {
      e.preventDefault();
      saveAyushData();
      MediTalk.showToast('AYUSH Dashavidha Pariksha saved to record.', 'success');
    });
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      saveAyushData();
      window.location.href = 'summary.html';
    });
  }
}

function saveAyushData() {
  const patient = MediKioskData.getCurrentPatient();
  if (!patient) return;

  const switchEl = document.getElementById('enableAyushSwitch');
  const notesEl = document.getElementById('ayushNotes');

  patient.ayush = {
    enabled: switchEl ? switchEl.checked : true,
    evaluatedAt: new Date().toISOString(),
    prakriti: getSelectVal('ayushPrakriti'),
    vikriti: getSelectVal('ayushVikriti'),
    sara: getSelectVal('ayushSara'),
    samhanana: getSelectVal('ayushSamhanana'),
    pramana: getSelectVal('ayushPramana'),
    satmya: getSelectVal('ayushSatmya'),
    satva: getSelectVal('ayushSatva'),
    aharaShakti: getSelectVal('ayushAharaShakti'),
    vyayamaShakti: getSelectVal('ayushVyayamaShakti'),
    vaya: getSelectVal('ayushVaya'),
    notes: notesEl ? notesEl.value.trim() : ''
  };

  patient.workflowStep = Math.max(patient.workflowStep || 1, 4);
  MediKioskData.saveCurrentPatient(patient);
}

function getSelectVal(id) {
  const el = document.getElementById(id);
  return el ? el.value : '';
}

function setSelectVal(id, val) {
  if (!val) return;
  const el = document.getElementById(id);
  if (!el) return;
  // Match exact or partial
  for (let opt of el.options) {
    if (opt.value === val || opt.value.startsWith(val.split(' ')[0])) {
      el.value = opt.value;
      return;
    }
  }
}
