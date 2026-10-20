/* =========================================================
   MediTalk — main.js
   Shared utility functions used across all pages
   ========================================================= */

'use strict';

// ── Navbar active link highlighting ──────────────────────
(function highlightNav() {
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link-mt').forEach(link => {
    const href = link.getAttribute('href') || '';
    if (href === page || (page === '' && href === 'index.html')) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
  });
})();

// ── Smooth scroll for in-page anchor links ───────────────
document.addEventListener('click', function (e) {
  const anchor = e.target.closest('a[href^="#"]');
  if (!anchor) return;
  const target = document.querySelector(anchor.getAttribute('href'));
  if (target) {
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    // close mobile navbar if open
    const navCollapse = document.getElementById('mainNav');
    if (navCollapse && navCollapse.classList.contains('show')) {
      const bsCollapse = bootstrap.Collapse.getInstance(navCollapse);
      if (bsCollapse) bsCollapse.hide();
    }
  }
});

// ── Toast notification helper ─────────────────────────────
/**
 * Show a simple toast message.
 * @param {string} message
 * @param {'info'|'success'|'warning'|'danger'} type
 * @param {number} duration  ms
 */
function showToast(message, type = 'info', duration = 3500) {
  let container = document.getElementById('mt-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'mt-toast-container';
    container.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:.5rem;max-width:340px;';
    document.body.appendChild(container);
  }

  const colors = {
    info:    { bg: '#e8f0fb', border: '#1a5fa8', text: '#134d8c', icon: 'bi-info-circle-fill' },
    success: { bg: '#dcfce7', border: '#16a34a', text: '#14532d', icon: 'bi-check-circle-fill' },
    warning: { bg: '#fef3c7', border: '#d97706', text: '#92400e', icon: 'bi-exclamation-triangle-fill' },
    danger:  { bg: '#fee2e2', border: '#dc2626', text: '#7f1d1d', icon: 'bi-x-circle-fill' },
  };
  const c = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.style.cssText = `
    display:flex;align-items:flex-start;gap:.75rem;
    background:${c.bg};border:1px solid ${c.border};color:${c.text};
    border-radius:10px;padding:.75rem 1rem;
    box-shadow:0 4px 16px rgba(0,0,0,.1);
    animation:slideInRight .25s ease;
    font-size:.9rem;font-family:inherit;line-height:1.5;
  `;
  toast.innerHTML = `<i class="bi ${c.icon}" style="font-size:1.1rem;flex-shrink:0;margin-top:1px;"></i><span>${message}</span>`;
  container.appendChild(toast);

  // auto-remove
  setTimeout(() => {
    toast.style.transition = 'opacity .3s, transform .3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

// Inject keyframe if not present
if (!document.getElementById('mt-anim-style')) {
  const s = document.createElement('style');
  s.id = 'mt-anim-style';
  s.textContent = '@keyframes slideInRight{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}';
  document.head.appendChild(s);
}

// ── Format time helper ────────────────────────────────────
function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ── Expose helpers globally ───────────────────────────────
window.MediTalk = { showToast, formatTime };
