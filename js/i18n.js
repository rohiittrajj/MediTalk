/* =========================================================
   MediTalk — i18n.js
   Multilingual Support: English (en), Hindi (hi), Hinglish (hi-en)
   JavaScript dictionary translation engine + persistent language selector
   ========================================================= */

'use strict';

const I18N_STORAGE_KEY = 'medikiosk_lang';

const TRANSLATIONS = {
  en: {
    // Navigation
    'nav.brand': 'MediTalk',
    'nav.home': 'Home',
    'nav.dashboard': 'Dashboard',
    'nav.register': '1. Register / Identify',
    'nav.case_taking': '2. AI Case-Taking',
    'nav.scan': '3. Document Scan',
    'nav.ayush': '4. AYUSH Mode',
    'nav.summary': '5. Medical Summary',
    'nav.doctor': 'Doctor Portal',
    'nav.signin': 'Staff Login',
    'nav.lang': 'Language',

    // Workflow Steps
    'workflow.title': 'MediTalk Clinical Workflow',
    'workflow.subtitle': 'Standardized 5-step clinical intake pipeline',
    'workflow.step1_title': 'Identify',
    'workflow.step1_desc': 'Patient details, ABHA ID & consent form',
    'workflow.step2_title': 'Converse',
    'workflow.step2_desc': 'AI case-taking & symptom interrogation',
    'workflow.step3_title': 'Scan',
    'workflow.step3_desc': 'Prescriptions & lab reports OCR',
    'workflow.step4_title': 'Consult & AYUSH',
    'workflow.step4_desc': 'Dashavidha Pariksha & red-flags check',
    'workflow.step5_title': 'Summarize & Share',
    'workflow.step5_desc': 'Printable summary & FHIR/ABDM record',

    // Common Buttons & Labels
    'btn.next': 'Continue to Next Step',
    'btn.back': 'Back',
    'btn.save_draft': 'Save Draft',
    'btn.print': 'Print Summary',
    'btn.pdf': 'Export PDF',
    'btn.edit': 'Edit Information',
    'btn.new_intake': 'Start New Patient Intake',
    'btn.verify_abha': 'Verify ABHA (Simulated)',
    'btn.voice_input': 'Speak into Mic',
    'btn.clear': 'Clear',
    'btn.send': 'Send',

    // Disclaimers & Alerts
    'alert.demo': 'Demonstration Environment — Frontend Healthcare AI Prototype. Data is stored in local browser session only.',
    'alert.redflag_title': 'CRITICAL RED-FLAG ALERT',
    'alert.redflag_body': 'The patient reported symptoms suggesting an emergency. Direct triage and immediate clinical attention required.',
    'alert.missing_info': 'Incomplete Patient Data Flagged',
    'alert.consent_req': 'Patient informed consent is mandatory prior to clinical documentation.',

    // Registration Form
    'reg.title': 'Patient Identification & Registration',
    'reg.subtitle': 'Step 1 of 5 — Capture demographics, ABHA ID, and clinical consent',
    'reg.name': 'Full Name',
    'reg.name_ph': 'Enter patient full name',
    'reg.age': 'Age (Years)',
    'reg.gender': 'Gender',
    'reg.gender_male': 'Male',
    'reg.gender_female': 'Female',
    'reg.gender_other': 'Other',
    'reg.phone': 'Mobile Number',
    'reg.phone_ph': '10-digit mobile number',
    'reg.abha': 'ABHA Health ID (Ayushman Bharat)',
    'reg.abha_ph': 'e.g. 91-4821-7392-5014',
    'reg.lang_pref': 'Preferred Consultation Language',
    'reg.emergency_contact': 'Emergency Contact Name & Phone',
    'reg.history': 'Known Medical Conditions',
    'reg.allergies': 'Known Drug / Food Allergies',
    'reg.allergies_ph': 'e.g. Penicillin, Sulfa, Dust, or type NKDA',
    'reg.consent_title': 'Digital Informed Consent',
    'reg.consent_text': 'I authorize MediTalk to record my symptoms, process my uploaded documents, and generate a pre-consultation medical summary for my attending physician under ABDM privacy standards.',

    // Case-Taking
    'case.title': 'AI Clinical Case-Taking',
    'case.subtitle': 'Step 2 of 5 — Guided symptom interrogation with voice and touch',
    'case.chief_complaint': 'Primary Chief Complaint',
    'case.chief_ph': 'What brings you to the clinic today? (e.g. Chest pain, high fever, cough)',
    'case.duration': 'Duration of Symptoms',
    'case.severity': 'Severity Scale (1 to 10)',
    'case.symptoms_select': 'Select Associated Symptoms',
    'case.current_meds': 'Current Medications Being Taken',
    'case.current_meds_ph': 'List tablet names, doses or frequencies if known',

    // Document Scanning
    'scan.title': 'Medical Document Scanning & OCR',
    'scan.subtitle': 'Step 3 of 5 — Digitally attach prescriptions, lab reports and discharge summaries',
    'scan.ocr_notice': 'Simulated OCR Engine (Demo) — Review and edit all extracted clinical values before saving',
    'scan.doc_type': 'Document Classification',
    'scan.facility': 'Doctor / Hospital / Lab Name',
    'scan.date': 'Document Date',
    'scan.findings': 'Extracted Findings / Test Results',
    'scan.meds': 'Extracted Prescription / Medications',

    // AYUSH
    'ayush.title': 'AYUSH Assessment — Dashavidha Pariksha',
    'ayush.subtitle': 'Step 4 of 5 — Tenfold comprehensive Ayurvedic clinical examination',
    'ayush.toggle': 'Include AYUSH Dashavidha Pariksha in Clinical Summary',

    // Summary
    'summary.title': 'Pre-Consultation Medical Summary',
    'summary.subtitle': 'Step 5 of 5 — Verified patient clinical intake sheet for the attending doctor',
    'summary.review_status': 'Clinician Review Status',
    'summary.doctor_notes': 'Attending Doctor Review & Clinical Impression',
    'summary.disclaimer': 'MediTalk is an assistive clinical documentation platform. Final diagnosis and prescriptions rest solely with the licensed medical practitioner.'
  },

  hi: {
    // Navigation
    'nav.brand': 'मेडीटॉक',
    'nav.home': 'होम',
    'nav.dashboard': 'डैशबोर्ड',
    'nav.register': '1. पंजीकरण / पहचान',
    'nav.case_taking': '2. एआई केस-टेकिंग',
    'nav.scan': '3. दस्तावेज़ स्कैन',
    'nav.ayush': '4. आयुष मोड',
    'nav.summary': '5. मेडिकल सारांश',
    'nav.doctor': 'डॉक्टर पोर्टल',
    'nav.signin': 'स्टाफ लॉगिन',
    'nav.lang': 'भाषा',

    // Workflow Steps
    'workflow.title': 'मेडीटॉक क्लिनिकल वर्कफ़्लो',
    'workflow.subtitle': 'मानकीकृत 5-चरणीय रोगी प्रवेश एवं पूर्व-परामर्श प्रक्रिया',
    'workflow.step1_title': 'पहचान (Identify)',
    'workflow.step1_desc': 'रोगी विवरण, आभा (ABHA) आईडी एवं सहमति पत्र',
    'workflow.step2_title': 'संवाद (Converse)',
    'workflow.step2_desc': 'एआई केस-टेकिंग एवं लक्षणों की पूछताछ',
    'workflow.step3_title': 'स्कैन (Scan)',
    'workflow.step3_desc': 'दवा की पर्ची व लैब रिपोर्ट ओसीआर',
    'workflow.step4_title': 'परामर्श व आयुष (Consult)',
    'workflow.step4_desc': 'दशविध परीक्षा एवं रेड-फ्लैग चेतावनी जांच',
    'workflow.step5_title': 'सारांश व साझा (Summarize)',
    'workflow.step5_desc': 'प्रिंट-सक्षम सारांश एवं FHIR/ABDM रिकॉर्ड',

    // Common Buttons & Labels
    'btn.next': 'अगले चरण पर जाएं',
    'btn.back': 'पीछे जाएं',
    'btn.save_draft': 'ड्राफ्ट सहेजें',
    'btn.print': 'सारांश प्रिंट करें',
    'btn.pdf': 'पीडीएफ निर्यात करें',
    'btn.edit': 'जानकारी संपादित करें',
    'btn.new_intake': 'नया मरीज पंजीकरण',
    'btn.verify_abha': 'आभा सत्यापित करें (सिम्युलेटेड)',
    'btn.voice_input': 'माइक में बोलें',
    'btn.clear': 'साफ़ करें',
    'btn.send': 'भेजें',

    // Disclaimers & Alerts
    'alert.demo': 'प्रदर्शन वातावरण — फ्रंटएंड हेल्थकेयर एआई सिस्टम। डेटा स्थानीय ब्राउज़र मेमोरी में है।',
    'alert.redflag_title': 'अति-गंभीर रेड-फ्लैग चेतावनी (Red-Flag Alert)',
    'alert.redflag_body': 'रोगी ने आपातकालीन लक्षण दर्ज किए हैं। तत्काल चिकित्सीय ध्यान और प्राथमिक जांच आवश्यक है।',
    'alert.missing_info': 'अधूरी मरीज जानकारी चिह्नित',
    'alert.consent_req': 'क्लिनिकल प्रलेखन से पूर्व मरीज की सूचित सहमति अनिवार्य है।',

    // Registration Form
    'reg.title': 'रोगी पहचान एवं पंजीकरण',
    'reg.subtitle': 'चरण 1 / 5 — व्यक्तिगत विवरण, आभा आईडी और सहमति पत्र दर्ज करें',
    'reg.name': 'पूरा नाम',
    'reg.name_ph': 'रोगी का पूरा नाम दर्ज करें',
    'reg.age': 'उम्र (वर्ष)',
    'reg.gender': 'लिंग',
    'reg.gender_male': 'पुरुष',
    'reg.gender_female': 'महिला',
    'reg.gender_other': 'अन्य',
    'reg.phone': 'मोबाइल नंबर',
    'reg.phone_ph': '10 अंकों का मोबाइल नंबर',
    'reg.abha': 'आभा (ABHA) हेल्थ आईडी',
    'reg.abha_ph': 'जैसे 91-4821-7392-5014',
    'reg.lang_pref': 'परामर्श हेतु पसंदीदा भाषा',
    'reg.emergency_contact': 'आपातकालीन संपर्क नाम व नंबर',
    'reg.history': 'पूर्व चिकित्सीय बीमारियां (बीपी/शुगर/अस्थमा)',
    'reg.allergies': 'दवा या भोजन से एलर्जी',
    'reg.allergies_ph': 'जैसे पेनिसिलिन, सल्फा या कोई एलर्जी नहीं (NKDA)',
    'reg.consent_title': 'डिजिटल सूचित सहमति',
    'reg.consent_text': 'मैं मेडीटॉक को मेरे लक्षण रिकॉर्ड करने, दस्तावेज़ पढ़ने और डॉक्टर हेतु मेडिकल सारांश तैयार करने की सहमति देता/देती हूँ।',

    // Case-Taking
    'case.title': 'एआई क्लिनिकल केस-टेकिंग',
    'case.subtitle': 'चरण 2 / 5 — आवाज़ व स्पर्श द्वारा लक्षणों का विवरण',
    'case.chief_complaint': 'मुख्य बीमारी / शिकायत (Chief Complaint)',
    'case.chief_ph': 'आज आप अस्पताल किस मुख्य समस्या के कारण आए हैं? (जैसे सीने में दर्द, तेज़ बुखार, खांसी)',
    'case.duration': 'समस्या कितने समय से है (अवधि)',
    'case.severity': 'दर्द / परेशानी की तीव्रता (1 से 10)',
    'case.symptoms_select': 'जुड़े हुए अन्य लक्षण चुनें',
    'case.current_meds': 'वर्तमान में ली जा रही दवाइयां',
    'case.current_meds_ph': 'दवाओं के नाम व खुराक यदि ज्ञात हों',

    // Document Scanning
    'scan.title': 'मेडिकल दस्तावेज़ स्कैन एवं ओसीआर',
    'scan.subtitle': 'चरण 3 / 5 — पर्ची, लैब रिपोर्ट और डिस्चार्ज समरी जोड़ें',
    'scan.ocr_notice': 'सिम्युलेटेड ओसीआर इंजन (डेमो) — कृपया सहेजने से पूर्व निकाले गए विवरण की जांच व संपादन करें',
    'scan.doc_type': 'दस्तावेज़ का प्रकार',
    'scan.facility': 'डॉक्टर / अस्पताल / लैब का नाम',
    'scan.date': 'दस्तावेज़ की तारीख',
    'scan.findings': 'जांच के परिणाम व निष्कर्ष',
    'scan.meds': 'पर्ची में लिखी दवाइयां',

    // AYUSH
    'ayush.title': 'आयुष परीक्षण — दशविध परीक्षा',
    'ayush.subtitle': 'चरण 4 / 5 — 10-चरणीय संपूर्ण आयुर्वेदिक क्लिनिकल जांच',
    'ayush.toggle': 'मेडिकल सारांश में आयुष दशविध परीक्षा शामिल करें',

    // Summary
    'summary.title': 'पूर्व-परामर्श मेडिकल सारांश (Medical Summary)',
    'summary.subtitle': 'चरण 5 / 5 — उपस्थित चिकित्सक हेतु सत्यापित क्लिनिकल सारांश शीट',
    'summary.review_status': 'डॉक्टर समीक्षा स्थिति',
    'summary.doctor_notes': 'उपस्थित चिकित्सक की टिप्पणी व निर्देश',
    'summary.disclaimer': 'मेडीटॉक एक सहायक क्लिनिकल प्रलेखन प्रणाली है। अंतिम निदान व दवा केवल प्रमाणित डॉक्टर द्वारा ही मान्य है।'
  },

  'hi-en': {
    // Navigation
    'nav.brand': 'MediTalk',
    'nav.home': 'Home',
    'nav.dashboard': 'Dashboard',
    'nav.register': '1. Patient Registration',
    'nav.case_taking': '2. AI Case-Taking',
    'nav.scan': '3. Document Scan',
    'nav.ayush': '4. AYUSH Assessment',
    'nav.summary': '5. Medical Summary',
    'nav.doctor': 'Doctor Portal',
    'nav.signin': 'Staff Login',
    'nav.lang': 'Language / भाषा',

    // Workflow Steps
    'workflow.title': 'MediTalk Complete Workflow',
    'workflow.subtitle': 'Standardized 5-step clinical intake workflow',
    'workflow.step1_title': 'Identify (Pehchan)',
    'workflow.step1_desc': 'Patient details, ABHA ID & Consent form',
    'workflow.step2_title': 'Converse (Baatcheet)',
    'workflow.step2_desc': 'AI case-taking & symptoms discussion',
    'workflow.step3_title': 'Scan (Dastavez)',
    'workflow.step3_desc': 'Prescriptions & lab reports OCR scanning',
    'workflow.step4_title': 'Consult & AYUSH',
    'workflow.step4_desc': 'Dashavidha Pariksha & Red-flags identification',
    'workflow.step5_title': 'Summarize & Share',
    'workflow.step5_desc': 'Printable medical summary & ABDM/FHIR share',

    // Common Buttons & Labels
    'btn.next': 'Next Step Par Jayein',
    'btn.back': 'Wapas (Back)',
    'btn.save_draft': 'Draft Save Karein',
    'btn.print': 'Summary Print Karein',
    'btn.pdf': 'PDF Export Karein',
    'btn.edit': 'Details Edit Karein',
    'btn.new_intake': 'Naya Patient Start Karein',
    'btn.verify_abha': 'Verify ABHA (Simulated)',
    'btn.voice_input': 'Mic me bolein',
    'btn.clear': 'Clear Karein',
    'btn.send': 'Send',

    // Disclaimers & Alerts
    'alert.demo': 'Demo Environment — Frontend Healthcare AI Platform. Data local browser storage me hi save rehta hai.',
    'alert.redflag_title': 'EMERGENCY RED-FLAG ALERT',
    'alert.redflag_body': 'Patient ne emergency symptoms bataye hain. Turant emergency triage & doctor consultation required.',
    'alert.missing_info': 'Incomplete Patient Details Detect Huyi Hain',
    'alert.consent_req': 'Patient consent form verify hona zaroori hai.',

    // Registration Form
    'reg.title': 'Patient Identification & Registration',
    'reg.subtitle': 'Step 1 of 5 — Demographics, ABHA ID aur consent form fill karein',
    'reg.name': 'Pura Naam (Full Name)',
    'reg.name_ph': 'Patient ka full name likhein',
    'reg.age': 'Umar (Age in Years)',
    'reg.gender': 'Gender (Ling)',
    'reg.gender_male': 'Male (Purush)',
    'reg.gender_female': 'Female (Mahila)',
    'reg.gender_other': 'Other',
    'reg.phone': 'Mobile Number',
    'reg.phone_ph': '10-digit mobile number',
    'reg.abha': 'ABHA Health ID',
    'reg.abha_ph': 'Jaise 91-4821-7392-5014',
    'reg.lang_pref': 'Consultation Language Preference',
    'reg.emergency_contact': 'Emergency Contact Person & Phone',
    'reg.history': 'Known Medical Conditions (BP, Diabetes, etc.)',
    'reg.allergies': 'Known Drug / Food Allergies',
    'reg.allergies_ph': 'Jaise Penicillin, Sulfa ya NKDA (No Known Allergies)',
    'reg.consent_title': 'Digital Consent Form',
    'reg.consent_text': 'Main MediTalk ko apne symptoms record karne, reports process karne aur doctor ke liye pre-consult summary banane ki consent deta/deti hoon.',

    // Case-Taking
    'case.title': 'AI Case-Taking (Symptom Intake)',
    'case.subtitle': 'Step 2 of 5 — Voice aur touch se apne symptoms record karein',
    'case.chief_complaint': 'Chief Complaint (Main dikkat kya hai?)',
    'case.chief_ph': 'Aapko clinic aane ki main wajah kya hai? (e.g. Seene me dard, Tez bukhar, Khansi)',
    'case.duration': 'Duration (Kitne dino se takleef hai?)',
    'case.severity': 'Severity Scale (1 se 10 tak dard/takleef)',
    'case.symptoms_select': 'Sath me aur kya symptoms hain?',
    'case.current_meds': 'Currently chal rahi dawaiyan (Medications)',
    'case.current_meds_ph': 'Medicines ke naam aur dosage likhein',

    // Document Scanning
    'scan.title': 'Medical Documents Scan & OCR',
    'scan.subtitle': 'Step 3 of 5 — Prescription aur Lab reports upload karein',
    'scan.ocr_notice': 'Simulated OCR Engine (Demo) — Save karne se pehle extracted details verify aur edit karein',
    'scan.doc_type': 'Document Type (Prescription / Lab / Discharge)',
    'scan.facility': 'Doctor ya Hospital ka Naam',
    'scan.date': 'Document Date',
    'scan.findings': 'Extracted Findings aur Lab Test Results',
    'scan.meds': 'Extracted Medicines List',

    // AYUSH
    'ayush.title': 'AYUSH Dashavidha Pariksha',
    'ayush.subtitle': 'Step 4 of 5 — 10 Ayurvedic clinical categories ka assessment',
    'ayush.toggle': 'Medical Summary me AYUSH Assessment add karein',

    // Summary
    'summary.title': 'Pre-Consultation Medical Summary',
    'summary.subtitle': 'Step 5 of 5 — Doctor ke consultation ke liye structured summary sheet',
    'summary.review_status': 'Doctor Review Status',
    'summary.doctor_notes': 'Attending Doctor Review & Clinical Notes',
    'summary.disclaimer': 'MediTalk pre-consultation documentation tool hai. Final diagnosis aur prescription doctor hi pradan karenge.'
  }
};

const I18n = {
  currentLang: 'en',

  init() {
    const saved = localStorage.getItem(I18N_STORAGE_KEY);
    if (saved && (saved === 'en' || saved === 'hi' || saved === 'hi-en')) {
      this.currentLang = saved;
    } else {
      this.currentLang = 'en';
    }
    this.applyLanguage(this.currentLang);
    this.renderLanguageSelector();
  },

  setLanguage(lang) {
    if (!TRANSLATIONS[lang]) return;
    this.currentLang = lang;
    localStorage.setItem(I18N_STORAGE_KEY, lang);
    this.applyLanguage(lang);
    this.updateActiveSelectorButtons();
    // Dispatch custom event so pages can re-render dynamic content
    window.dispatchEvent(new CustomEvent('meditalk:langChanged', { detail: { lang } }));
    window.dispatchEvent(new CustomEvent('medikiosk:langChanged', { detail: { lang } }));
  },

  t(key, fallback = '') {
    const dict = TRANSLATIONS[this.currentLang] || TRANSLATIONS.en;
    if (dict[key] !== undefined) return dict[key];
    const enDict = TRANSLATIONS.en;
    return enDict[key] !== undefined ? enDict[key] : (fallback || key);
  },

  applyLanguage(lang) {
    // Translate all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const translation = this.t(key);
      if (translation) {
        el.textContent = translation;
      }
    });

    // Translate all elements with data-i18n-html attribute
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      const key = el.getAttribute('data-i18n-html');
      const translation = this.t(key);
      if (translation) {
        el.innerHTML = translation;
      }
    });

    // Translate input placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const translation = this.t(key);
      if (translation) {
        el.setAttribute('placeholder', translation);
      }
    });

    // Translate document title if marked
    const titleEl = document.querySelector('title[data-i18n-title]');
    if (titleEl) {
      const key = titleEl.getAttribute('data-i18n-title');
      const translation = this.t(key);
      if (translation) document.title = translation + ' — MediTalk';
    }
  },

  renderLanguageSelector() {
    // Check if a container #langSelectorContainer exists or inject into .navbar .container
    let container = document.getElementById('langSelectorContainer');
    if (!container) {
      const navCollapse = document.getElementById('mainNav');
      if (navCollapse) {
        container = document.createElement('div');
        container.id = 'langSelectorContainer';
        container.className = 'd-flex align-items-center ms-lg-3 my-2 my-lg-0';
        navCollapse.appendChild(container);
      }
    }

    if (container) {
      container.innerHTML = `
        <div class="btn-group btn-group-sm" role="group" aria-label="Language Selector">
          <button type="button" class="btn btn-outline-primary btn-lang ${this.currentLang === 'en' ? 'active' : ''}" data-lang="en" title="English">
            EN
          </button>
          <button type="button" class="btn btn-outline-primary btn-lang ${this.currentLang === 'hi' ? 'active' : ''}" data-lang="hi" title="Hindi (हिंदी)">
            हिंदी
          </button>
          <button type="button" class="btn btn-outline-primary btn-lang ${this.currentLang === 'hi-en' ? 'active' : ''}" data-lang="hi-en" title="Hinglish (Hindi+English)">
            Hinglish
          </button>
        </div>
      `;

      container.querySelectorAll('.btn-lang').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const targetLang = btn.getAttribute('data-lang');
          I18n.setLanguage(targetLang);
        });
      });
    }
  },

  updateActiveSelectorButtons() {
    document.querySelectorAll('.btn-lang').forEach(btn => {
      const lang = btn.getAttribute('data-lang');
      if (lang === this.currentLang) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  I18n.init();
});

window.I18n = I18n;
