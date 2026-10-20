/* =========================================================
   MediTalk — data-store.js
   Centralized data management for MediTalk Healthcare Platform
   Vanilla JS + localStorage persistence (frontend demonstration only)
   ========================================================= */

'use strict';

const STORAGE_KEYS = {
  CURRENT_PATIENT: 'medikiosk_current_patient',
  PATIENTS_LIST: 'medikiosk_patients_list',
  CURRENT_LANGUAGE: 'medikiosk_lang',
};

// Initial default patient for instant demonstration
const DEFAULT_PATIENT = {
  id: 'MT-2026-0842',
  registeredAt: new Date().toISOString(),
  workflowStep: 2, // 1: Identify, 2: Converse, 3: Scan, 4: Consult, 5: Summarize
  demographics: {
    fullName: 'Rajesh Kumar Verma',
    age: 46,
    gender: 'Male',
    phone: '+91 98765 43210',
    preferredLanguage: 'hi-en',
    abhaId: '91-4821-7392-5014',
    abhaStatus: 'Verified (Simulated ABDM Sandbox)',
    emergencyContactName: 'Sunita Verma',
    emergencyContactPhone: '+91 98765 43211',
    consentGiven: true,
    consentTimestamp: new Date().toISOString()
  },
  caseTaking: {
    chiefComplaint: 'Severe chest tightness and persistent dry cough for 3 days',
    durationValue: '3',
    durationUnit: 'days',
    severity: 8, // 1 - 10
    symptoms: [
      'Chest tightness / discomfort',
      'Dry cough',
      'Mild shortness of breath on exertion',
      'Fatigue'
    ],
    symptomNotes: 'Symptoms worsen late at night and during cold weather. Patient feels sudden heaviness in mid-chest.',
    pastMedicalHistory: ['Hypertension (3 years)', 'Type 2 Diabetes (Borderline)'],
    pastHistoryNotes: 'Takes Telmisartan 40mg occasionally; irregular medication compliance.',
    currentMedications: 'Tab Telmisartan 40mg (OD - irregular), Paracetamol 650mg SOS',
    allergies: 'Penicillin (Skin urticaria & itching reported in 2018)',
    redFlagsDetected: [
      'Chest tightness / discomfort reported with severity 8/10',
      'Shortness of breath on exertion'
    ],
    redFlagStatus: 'HIGH_ALERT' // 'CLEAR' | 'MODERATE' | 'HIGH_ALERT'
  },
  ayush: {
    enabled: true,
    evaluatedAt: new Date().toISOString(),
    prakriti: 'Vata-Pitta',
    vikriti: 'Vata-Kapha Dusti (Pranavaha Srotas involved)',
    sara: 'Madhyama Sara (Moderate tissue excellence)',
    samhanana: 'Madhyama (Medium body compactness)',
    pramana: 'Pramana Normal (Height 172cm, Wt 76kg, BMI 25.7)',
    satmya: 'Vyayama-Alpa Satmya (Accustomed to sedentary routine)',
    satva: 'Madhyama Satva (Moderate mental resilience, mild anxiety)',
    aharaShakti: 'Manda Agni (Low/Sluggish digestion, post-prandial fullness)',
    vyayamaShakti: 'Avara (Low physical exercise endurance)',
    vaya: 'Madhyama Vaya (46 years - Middle adulthood)',
    notes: 'Pranavaha srotodusti observed. Advised mild Ushna deepana diet and avoidance of cold exposure.'
  },
  documents: [
    {
      id: 'doc-001',
      title: 'Previous Physician Prescription',
      category: 'Prescription',
      fileName: 'Rx_DrSharma_Clinic.pdf',
      uploadDate: '2026-10-18',
      simulatedOcr: {
        facilityName: 'Metro Health Clinic, New Delhi',
        doctorName: 'Dr. A. K. Sharma (MD Internal Med)',
        date: '2026-09-15',
        extractedDiagnosis: 'Essential Hypertension - Stage 1',
        extractedMedications: 'Tab Telmisartan 40mg OD mornings x 30 days',
        extractedNotes: 'Advised sodium restriction, regular BP monitoring, and repeat ECG if chest tightness recurs.'
      }
    },
    {
      id: 'doc-002',
      title: 'Recent Lipid & Glucose Profile',
      category: 'Laboratory Report',
      fileName: 'Lab_Pathology_Report.png',
      uploadDate: '2026-10-19',
      simulatedOcr: {
        facilityName: 'National Diagnostics Lab',
        doctorName: 'Dr. Neha Gupta (Pathologist)',
        date: '2026-10-10',
        extractedDiagnosis: 'Borderline Fasting Dysglycemia & Hypercholesterolemia',
        extractedMedications: 'N/A (Diagnostic report)',
        extractedNotes: 'Fasting Blood Sugar: 118 mg/dL (Elevated), HbA1c: 6.2%, Total Cholesterol: 224 mg/dL.'
      }
    }
  ],
  doctorReview: {
    status: 'Pending Review', // 'Pending Review' | 'Under Review' | 'Reviewed & Approved'
    doctorName: 'Dr. Sanjay K. Mehta, MBBS, MD',
    clinicName: 'MediTalk Consultation & Clinical Triage Center',
    reviewedAt: null,
    notes: '',
    provisionalImpression: 'Evaluate for Acute Coronary Syndrome vs. Bronchospastic cough. Immediate 12-lead ECG and Troponin-I advised given chest tightness & hypertension.'
  }
};

// Demonstration queued patients for Doctor Dashboard
const INITIAL_PATIENTS_QUEUE = [
  DEFAULT_PATIENT,
  {
    id: 'MT-2026-0841',
    registeredAt: '2026-10-20T10:15:00Z',
    workflowStep: 5,
    demographics: {
      fullName: 'Anita Devi',
      age: 34,
      gender: 'Female',
      phone: '+91 98112 33445',
      preferredLanguage: 'hi',
      abhaId: '91-3214-5567-8890',
      abhaStatus: 'Verified (Simulated ABDM Sandbox)',
      emergencyContactName: 'Ramesh Devi',
      emergencyContactPhone: '+91 98112 33446',
      consentGiven: true,
      consentTimestamp: '2026-10-20T10:16:00Z'
    },
    caseTaking: {
      chiefComplaint: 'High grade fever with severe joint pain and headache for 4 days',
      durationValue: '4',
      durationUnit: 'days',
      severity: 7,
      symptoms: ['High fever (102.5°F)', 'Severe knee and wrist joint pains', 'Retro-orbital headache', 'Nausea'],
      symptomNotes: 'Fever accompanied by intense chills. No cough or burning micturition.',
      pastMedicalHistory: ['Hypothyroidism'],
      pastHistoryNotes: 'Takes Thyroxine 50mcg daily.',
      currentMedications: 'Tab Thyroxine 50mcg OD, Tab Paracetamol 650mg TDS',
      allergies: 'No known drug allergies (NKDA)',
      redFlagsDetected: ['High fever > 102°F with severe joint arthralgia (Check for Chikungunya / Dengue)'],
      redFlagStatus: 'MODERATE'
    },
    ayush: {
      enabled: false,
      prakriti: '', vikriti: '', sara: '', samhanana: '', pramana: '',
      satmya: '', satva: '', aharaShakti: '', vyayamaShakti: '', vaya: '', notes: ''
    },
    documents: [
      {
        id: 'doc-003',
        title: 'Complete Blood Count (CBC)',
        category: 'Laboratory Report',
        fileName: 'CBC_Report_Anita.pdf',
        uploadDate: '2026-10-20',
        simulatedOcr: {
          facilityName: 'City Path Care',
          doctorName: 'Dr. V. Rao',
          date: '2026-10-20',
          extractedDiagnosis: 'Thrombocytopenia (Platelet: 98,000 /uL), Normal Hb: 12.4',
          extractedMedications: 'N/A',
          extractedNotes: 'Platelet count depressed. Dengue NS1 Ag rapid test reactive.'
        }
      }
    ],
    doctorReview: {
      status: 'Reviewed & Approved',
      doctorName: 'Dr. Sanjay K. Mehta, MBBS, MD',
      clinicName: 'MediTalk Consultation & Clinical Triage Center',
      reviewedAt: '2026-10-20T11:45:00Z',
      notes: 'Advised oral hydration, platelet count monitoring after 24 hrs. Paracetamol only; avoid NSAIDs.',
      provisionalImpression: 'Suspected Dengue Fever with mild thrombocytopenia.'
    }
  },
  {
    id: 'MT-2026-0839',
    registeredAt: '2026-10-19T14:30:00Z',
    workflowStep: 5,
    demographics: {
      fullName: 'Mohammad Tariq',
      age: 62,
      gender: 'Male',
      phone: '+91 97654 32190',
      preferredLanguage: 'en',
      abhaId: '91-7788-9900-1122',
      abhaStatus: 'Verified (Simulated ABDM Sandbox)',
      emergencyContactName: 'Farhan Tariq',
      emergencyContactPhone: '+91 97654 32191',
      consentGiven: true,
      consentTimestamp: '2026-10-19T14:32:00Z'
    },
    caseTaking: {
      chiefComplaint: 'Routine diabetes check-up and burning sensation in bilateral feet',
      durationValue: '2',
      durationUnit: 'months',
      severity: 4,
      symptoms: ['Bilateral feet numbness & tingling', 'Excessive thirst', 'Nocturia (waking 3 times)'],
      symptomNotes: 'Tingling is worse at bedtime. No ulcers or skin breakdown.',
      pastMedicalHistory: ['Type 2 Diabetes Mellitus (8 years)', 'Dyslipidemia'],
      pastHistoryNotes: 'Takes Metformin 1000mg twice daily.',
      currentMedications: 'Tab Metformin 1000mg BD, Tab Atorvastatin 20mg HS',
      allergies: 'Sulfa drugs (Skin peeling & rash)',
      redFlagsDetected: [],
      redFlagStatus: 'CLEAR'
    },
    ayush: {
      enabled: true,
      evaluatedAt: '2026-10-19T14:40:00Z',
      prakriti: 'Kapha-Pitta',
      vikriti: 'Kaphaja Prameha / Pittavrita Vata',
      sara: 'Meda Sara (Adipose tissue prominence)',
      samhanana: 'Pravara (Robust heavy body frame)',
      pramana: 'BMI 28.4 (Overweight category)',
      satmya: 'Madhura & Snigdha Satmya (Habituated to rich sweets)',
      satva: 'Pravara Satva',
      aharaShakti: 'Tikshnagni (High hunger / intense appetite)',
      vyayamaShakti: 'Avara (Sedentary lifestyle)',
      vaya: 'Vardhakya (62 yrs)',
      notes: 'Prameha line of treatment. Recommended daily walking, Yava (barley) diet, and Triphala decoction.'
    },
    documents: [],
    doctorReview: {
      status: 'Reviewed & Approved',
      doctorName: 'Dr. Sanjay K. Mehta, MBBS, MD',
      clinicName: 'MediTalk Consultation & Clinical Triage Center',
      reviewedAt: '2026-10-19T15:20:00Z',
      notes: 'Diabetic peripheral neuropathy suspected. Added Methylcobalamin + Pregabalin. Advised foot care inspection daily.',
      provisionalImpression: 'T2DM with early diabetic sensory polyneuropathy.'
    }
  }
];

// ── Red-Flag Clinical Rules Engine ────────────────────────
const RED_FLAG_RULES = [
  {
    category: 'Cardiovascular',
    keywords: ['chest pain', 'chest tightness', 'chest pressure', 'heart pain', 'left arm pain', 'jaw pain', 'sweating with chest'],
    message: 'Potential Acute Coronary Syndrome or Cardiac Ischemia warning.',
    severity: 'HIGH_ALERT'
  },
  {
    category: 'Respiratory',
    keywords: ['cannot breathe', 'difficulty breathing', 'severe breathlessness', 'shortness of breath', 'gasping', 'blue lips', 'stridor'],
    message: 'Severe respiratory distress requiring immediate oxygenation & triage.',
    severity: 'HIGH_ALERT'
  },
  {
    category: 'Neurological',
    keywords: ['slurred speech', 'facial drooping', 'sudden weakness', 'paralysis', 'unconscious', 'loss of consciousness', 'seizure', 'worst headache of life'],
    message: 'Potential Acute Stroke or Intracranial Event warning (FAST protocol).',
    severity: 'HIGH_ALERT'
  },
  {
    category: 'Systemic / Sepsis',
    keywords: ['blood in vomit', 'vomiting blood', 'coughing blood', 'severe bleeding', 'uncontrolled bleed', 'fever with confusion'],
    message: 'Active hemorrhage or severe systemic infection warning.',
    severity: 'HIGH_ALERT'
  },
  {
    category: 'High Fever',
    keywords: ['fever 103', 'fever 104', 'fever above 103', 'high grade fever'],
    message: 'Hyperpyrexia — monitor for febrile encephalopathy or severe bacteremia.',
    severity: 'MODERATE'
  }
];

// ── Data Store Helper Class ───────────────────────────────
const DataStore = {
  // Initialize storage if empty
  init() {
    if (!localStorage.getItem(STORAGE_KEYS.CURRENT_PATIENT)) {
      this.saveCurrentPatient(DEFAULT_PATIENT);
    }
    if (!localStorage.getItem(STORAGE_KEYS.PATIENTS_LIST)) {
      this.savePatientsList(INITIAL_PATIENTS_QUEUE);
    }
  },

  // Get active session patient
  getCurrentPatient() {
    this.init();
    try {
      const data = localStorage.getItem(STORAGE_KEYS.CURRENT_PATIENT);
      return data ? JSON.parse(data) : DEFAULT_PATIENT;
    } catch (e) {
      console.error('Error reading current patient:', e);
      return DEFAULT_PATIENT;
    }
  },

  // Save active session patient
  saveCurrentPatient(patient) {
    try {
      localStorage.setItem(STORAGE_KEYS.CURRENT_PATIENT, JSON.stringify(patient));
      // Sync into patient queue as well
      this.upsertPatientInQueue(patient);
    } catch (e) {
      console.error('Error saving current patient:', e);
    }
  },

  // Get full patients list (for doctor dashboard)
  getPatientsList() {
    this.init();
    try {
      const data = localStorage.getItem(STORAGE_KEYS.PATIENTS_LIST);
      return data ? JSON.parse(data) : INITIAL_PATIENTS_QUEUE;
    } catch (e) {
      console.error('Error reading patients list:', e);
      return INITIAL_PATIENTS_QUEUE;
    }
  },

  // Save full patients list
  savePatientsList(list) {
    try {
      localStorage.setItem(STORAGE_KEYS.PATIENTS_LIST, JSON.stringify(list));
    } catch (e) {
      console.error('Error saving patients list:', e);
    }
  },

  // Upsert a patient in the queue
  upsertPatientInQueue(patient) {
    if (!patient || !patient.id) return;
    const list = this.getPatientsList();
    const index = list.findIndex(p => p.id === patient.id);
    if (index >= 0) {
      list[index] = patient;
    } else {
      list.unshift(patient);
    }
    this.savePatientsList(list);
  },

  // Start a fresh patient intake
  startNewPatient(name = '', phone = '', preferredLanguage = 'en') {
    const randomId = 'MT-2026-' + Math.floor(1000 + Math.random() * 9000);
    const newPatient = {
      id: randomId,
      registeredAt: new Date().toISOString(),
      workflowStep: 1,
      demographics: {
        fullName: name,
        age: '',
        gender: '',
        phone: phone,
        preferredLanguage: preferredLanguage,
        abhaId: '',
        abhaStatus: 'Unlinked',
        emergencyContactName: '',
        emergencyContactPhone: '',
        consentGiven: false,
        consentTimestamp: null
      },
      caseTaking: {
        chiefComplaint: '',
        durationValue: '',
        durationUnit: 'days',
        severity: 5,
        symptoms: [],
        symptomNotes: '',
        pastMedicalHistory: [],
        pastHistoryNotes: '',
        currentMedications: '',
        allergies: '',
        redFlagsDetected: [],
        redFlagStatus: 'CLEAR'
      },
      ayush: {
        enabled: false,
        evaluatedAt: null,
        prakriti: '', vikriti: '', sara: '', samhanana: '', pramana: '',
        satmya: '', satva: '', aharaShakti: '', vyayamaShakti: '', vaya: '', notes: ''
      },
      documents: [],
      doctorReview: {
        status: 'Pending Review',
        doctorName: 'Dr. Sanjay K. Mehta, MBBS, MD',
        clinicName: 'MediTalk Consultation & Clinical Triage Center',
        reviewedAt: null,
        notes: '',
        provisionalImpression: ''
      }
    };
    this.saveCurrentPatient(newPatient);
    return newPatient;
  },

  // Detect red flags in text and symptom selections
  detectRedFlags(text = '', selectedSymptoms = [], severity = 5) {
    const detected = [];
    let highestSeverity = 'CLEAR';
    const lowerText = (text + ' ' + selectedSymptoms.join(' ')).toLowerCase();

    // Check keyword rules
    RED_FLAG_RULES.forEach(rule => {
      const matched = rule.keywords.some(kw => lowerText.includes(kw));
      if (matched) {
        detected.push(`[${rule.category}] ${rule.message}`);
        if (rule.severity === 'HIGH_ALERT') {
          highestSeverity = 'HIGH_ALERT';
        } else if (highestSeverity !== 'HIGH_ALERT') {
          highestSeverity = 'MODERATE';
        }
      }
    });

    // Check pain severity threshold
    if (Number(severity) >= 8) {
      detected.push(`[Severity Alert] Reported symptom severity is critically high (${severity}/10).`);
      if (highestSeverity === 'CLEAR') highestSeverity = 'MODERATE';
    }

    return {
      hasRedFlags: detected.length > 0,
      redFlags: detected,
      severityStatus: highestSeverity
    };
  },

  // Calculate missing clinical information
  detectMissingInformation(patient) {
    const missing = [];
    const demo = patient.demographics || {};
    const ct = patient.caseTaking || {};

    if (!demo.fullName) missing.push('Patient Full Name not recorded');
    if (!demo.age) missing.push('Age not specified');
    if (!demo.gender) missing.push('Gender not selected');
    if (!demo.phone) missing.push('Contact phone number missing');
    if (!demo.abhaId) missing.push('ABHA ID not provided or unverified');
    if (!demo.consentGiven) missing.push('Signed digital consent form pending');

    if (!ct.chiefComplaint) missing.push('Chief Complaint has not been articulated');
    if (!ct.durationValue) missing.push('Duration of symptoms is unspecified');
    if (!ct.symptoms || ct.symptoms.length === 0) missing.push('Specific associated symptoms checklist empty');
    if (!ct.pastMedicalHistory || ct.pastMedicalHistory.length === 0) missing.push('Past medical history not confirmed (or marked None)');
    if (!ct.currentMedications) missing.push('Current active medication list unrecorded');
    if (!ct.allergies) missing.push('Drug/Food allergy status unverified (Please verify NKDA)');

    if (!patient.documents || patient.documents.length === 0) {
      missing.push('No supportive clinical documents / lab reports attached');
    }

    return missing;
  },

  // Generate FHIR JSON resource representation (Simulated ABDM placeholder)
  generateFHIRBundle(patient) {
    const bundleId = 'bundle-' + (patient.id || 'MT-0000');
    return {
      resourceType: 'Bundle',
      id: bundleId,
      meta: {
        lastUpdated: new Date().toISOString(),
        profile: ['https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle']
      },
      identifier: {
        system: 'https://abdm.gov.in/facilities/meditalk',
        value: patient.id
      },
      type: 'document',
      timestamp: new Date().toISOString(),
      entry: [
        {
          fullUrl: `urn:uuid:composition-${patient.id}`,
          resource: {
            resourceType: 'Composition',
            status: 'final',
            type: {
              coding: [{
                system: 'http://snomed.info/sct',
                code: '371530004',
                display: 'Clinical consultation summary'
              }],
              text: 'MediTalk Clinical Intake Summary'
            },
            subject: {
              reference: `urn:uuid:patient-${patient.id}`,
              display: patient.demographics?.fullName || 'Patient'
            },
            encounter: {
              display: 'MediTalk Clinical Intake Encounter'
            },
            date: new Date().toISOString(),
            author: [{
              display: 'MediTalk Clinical AI Platform'
            }],
            title: 'Health History & Pre-Consultation Summary',
            section: [
              {
                title: 'Chief Complaint',
                text: { status: 'generated', div: `<div>${patient.caseTaking?.chiefComplaint || 'None'}</div>` }
              },
              {
                title: 'Allergies',
                text: { status: 'generated', div: `<div>${patient.caseTaking?.allergies || 'Unrecorded'}</div>` }
              },
              {
                title: 'Current Medications',
                text: { status: 'generated', div: `<div>${patient.caseTaking?.currentMedications || 'None reported'}</div>` }
              },
              {
                title: 'AYUSH Assessment (Dashavidha Pariksha)',
                text: { status: 'generated', div: `<div>Prakriti: ${patient.ayush?.prakriti || 'N/A'}, Vikriti: ${patient.ayush?.vikriti || 'N/A'}</div>` }
              }
            ]
          }
        },
        {
          fullUrl: `urn:uuid:patient-${patient.id}`,
          resource: {
            resourceType: 'Patient',
            identifier: [{
              type: { coding: [{ system: 'https://abdm.gov.in', code: 'ABHA' }] },
              value: patient.demographics?.abhaId || '91-XXXX-XXXX-XXXX'
            }],
            name: [{ text: patient.demographics?.fullName || 'Unknown' }],
            telecom: [{ system: 'phone', value: patient.demographics?.phone || '' }],
            gender: (patient.demographics?.gender || 'unknown').toLowerCase(),
            birthDate: patient.demographics?.age ? `${2026 - Number(patient.demographics.age)}-01-01` : undefined
          }
        }
      ]
    };
  }
};

// Expose globally under MediTalkData and backward-compatible alias MediKioskData
window.MediTalkData = DataStore;
window.MediKioskData = DataStore;
