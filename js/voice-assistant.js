/* =========================================================
   MediTalk — voice-assistant.js
   Web Speech API integration with graceful fallbacks
   =========================================================
   NOTE: Speech recognition is handled entirely in the browser.
   No external API, no paid service, no data is transmitted.
   ========================================================= */

'use strict';

// ── DOM references ────────────────────────────────────────
const micBtn        = document.getElementById('micBtn');
const micRipple     = document.getElementById('micRipple');
const statusText    = document.getElementById('voiceStatus');
const transcriptBox = document.getElementById('transcriptBox');
const clearTransBtn = document.getElementById('clearTranscriptBtn');
const langSelect    = document.getElementById('langSelect');
const noSupportMsg  = document.getElementById('noSupportMsg');
const historyList   = document.getElementById('voiceHistory');

// ── Check browser support ─────────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  // Hide the mic UI, show message
  if (micBtn) micBtn.disabled = true;
  if (noSupportMsg) noSupportMsg.style.display = 'block';
  if (statusText) statusText.textContent = 'Speech recognition is not supported in this browser.';
  console.warn('[MediTalk] SpeechRecognition API not available.');
}

// ── State ─────────────────────────────────────────────────
let recognition = null;
let isListening = false;
let sessionTranscript = '';
let voiceHistory = [];   // array of { text, time }

// ── Initialize recognition ────────────────────────────────
function initRecognition() {
  if (!SpeechRecognition) return null;

  const rec = new SpeechRecognition();
  rec.continuous     = true;
  rec.interimResults = true;
  rec.lang           = langSelect ? langSelect.value : 'en-IN';
  rec.maxAlternatives = 1;

  rec.onstart = () => {
    setListening(true);
    setStatus('Listening… speak clearly into your microphone.', 'active');
  };

  rec.onresult = (e) => {
    let interim = '';
    let final   = '';

    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) {
        final += t + ' ';
      } else {
        interim += t;
      }
    }

    sessionTranscript += final;
    updateTranscript(sessionTranscript, interim);
  };

  rec.onerror = (e) => {
    let msg = 'An error occurred.';
    switch (e.error) {
      case 'not-allowed':
        msg = 'Microphone access denied. Please allow microphone permission in your browser settings.';
        break;
      case 'no-speech':
        msg = 'No speech detected. Please speak closer to the microphone.';
        break;
      case 'network':
        msg = 'Network error. Speech recognition requires an internet connection in some browsers.';
        break;
      case 'audio-capture':
        msg = 'No microphone found. Please connect a microphone and try again.';
        break;
      default:
        msg = `Error: ${e.error}. Please try again.`;
    }
    setListening(false);
    setStatus(msg, 'error');
    MediTalk.showToast(msg, 'danger');
  };

  rec.onend = () => {
    if (isListening) {
      // Auto-restart if still supposed to be listening
      try { rec.start(); } catch (_) {}
    } else {
      setStatus('Click the microphone button to start speaking.', 'idle');
      // Save session to history
      if (sessionTranscript.trim()) {
        saveToHistory(sessionTranscript.trim());
      }
    }
  };

  return rec;
}

// ── UI helpers ────────────────────────────────────────────
function setListening(active) {
  isListening = active;
  if (micBtn) {
    micBtn.classList.toggle('listening', active);
    micBtn.setAttribute('aria-pressed', active.toString());
    micBtn.setAttribute('aria-label', active ? 'Stop listening' : 'Start voice input');
    micBtn.querySelector('i').className = active ? 'bi bi-stop-fill' : 'bi bi-mic-fill';
  }
  if (micRipple) {
    micRipple.style.display = active ? 'block' : 'none';
  }
}

function setStatus(msg, state) {
  if (!statusText) return;
  statusText.textContent = msg;
  statusText.style.color = state === 'active'
    ? 'var(--mt-teal)'
    : state === 'error'
      ? 'var(--mt-danger)'
      : 'var(--mt-text-muted)';
}

function updateTranscript(final, interim) {
  if (!transcriptBox) return;
  if (!final && !interim) {
    transcriptBox.innerHTML = '<span style="color:var(--mt-text-muted);font-style:italic;">Your words will appear here as you speak…</span>';
    return;
  }
  transcriptBox.innerHTML =
    `<span>${escapeHtml(final)}</span>` +
    (interim ? `<span style="color:var(--mt-text-muted);font-style:italic;">${escapeHtml(interim)}</span>` : '');
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function saveToHistory(text) {
  const entry = { text, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
  voiceHistory.unshift(entry);
  if (voiceHistory.length > 10) voiceHistory.pop();
  renderHistory();
}

function renderHistory() {
  if (!historyList) return;
  if (voiceHistory.length === 0) {
    historyList.innerHTML = '<li class="list-group-item text-muted" style="font-size:.88rem;">No recordings yet. Use the microphone to start.</li>';
    return;
  }
  historyList.innerHTML = voiceHistory.map((e, i) => `
    <li class="list-group-item d-flex justify-content-between align-items-start gap-2" style="font-size:.9rem;">
      <div>
        <span class="badge bg-primary-subtle text-primary me-2" style="font-size:.72rem;">${e.time}</span>
        ${escapeHtml(e.text.length > 120 ? e.text.slice(0, 120) + '…' : e.text)}
      </div>
      <button class="btn btn-sm btn-outline-danger" onclick="deleteHistory(${i})" aria-label="Delete this entry">
        <i class="bi bi-trash"></i>
      </button>
    </li>
  `).join('');
}

window.deleteHistory = function(index) {
  voiceHistory.splice(index, 1);
  renderHistory();
};

// ── Toggle recording ──────────────────────────────────────
function toggleRecording() {
  if (!SpeechRecognition) {
    MediTalk.showToast('Speech recognition is not supported in this browser. Try Chrome or Edge.', 'warning');
    return;
  }

  if (isListening) {
    // Stop
    isListening = false;
    if (recognition) { try { recognition.stop(); } catch (_) {} }
    setListening(false);
    setStatus('Recording stopped. Your transcript is shown below.', 'idle');
    MediTalk.showToast('Recording stopped.', 'info');
  } else {
    // Start
    sessionTranscript = '';
    updateTranscript('', '');
    recognition = initRecognition();
    if (!recognition) return;

    try {
      recognition.start();
    } catch (err) {
      setStatus('Could not start recording. Please try again.', 'error');
      MediTalk.showToast('Could not start microphone. Check permissions.', 'danger');
    }
  }
}

// ── Clear transcript ──────────────────────────────────────
if (clearTransBtn) {
  clearTransBtn.addEventListener('click', () => {
    if (isListening) {
      MediTalk.showToast('Stop recording before clearing.', 'warning');
      return;
    }
    sessionTranscript = '';
    updateTranscript('', '');
    MediTalk.showToast('Transcript cleared.', 'info');
  });
}

// ── Language change ───────────────────────────────────────
if (langSelect) {
  langSelect.addEventListener('change', () => {
    if (isListening) {
      MediTalk.showToast('Stop recording to change language.', 'warning');
      langSelect.value = recognition ? recognition.lang : 'en-IN';
    }
  });
}

// ── Mic button click ──────────────────────────────────────
if (micBtn) {
  micBtn.addEventListener('click', toggleRecording);
}

// ── Init page ─────────────────────────────────────────────
renderHistory();
setStatus('Click the microphone button to start speaking.', 'idle');
