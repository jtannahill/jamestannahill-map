// contact.jamestannahill.com behaviour. Served from 'self', so the CSP needs
// no per-script hashes: edit freely, no CloudFront policy change required.
(function () {
  'use strict';

  // ── SERVICE WORKER ────────────────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(e => console.warn('[SW]', e));
    });
  }

  // ── TOAST ─────────────────────────────────────────────────────────────
  function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._h);
    t._h = setTimeout(() => t.classList.remove('show'), 2500);
  }

  // Controls that only work with script stay hidden in the markup until now.
  document.querySelectorAll('[data-needs-js]').forEach(el => { el.hidden = false; });

  // ── WEB PUSH ──────────────────────────────────────────────────────────
  const VAPID_PUBLIC_KEY = 'BFIFhADuQ1yanvfGWtfEhtWCDRegFn98goWLzQbU8qgb95YOatlYKNkDg2kWIVNKzMinEMbV_Lulou5EmGxx4bY';

  function urlBase64ToUint8Array(b64) {
    const pad = '='.repeat((4 - b64.length % 4) % 4);
    const raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
    return new Uint8Array([...raw].map(c => c.charCodeAt(0)));
  }

  function updatePushBtn(subscribed) {
    const btn = document.getElementById('pushBtn');
    const lbl = document.getElementById('pushLabel');
    if (!btn || !lbl) return;
    lbl.textContent = subscribed ? 'Subscribed' : 'Get Updates';
    btn.classList.toggle('subscribed', subscribed);
  }

  async function initPush() {
    const btn = document.getElementById('pushBtn');
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
      // No push here (iOS Safari outside an installed web app): drop the cell so the grid has no empty block.
      btn?.remove();
      return;
    }
    if (btn) btn.hidden = false;
    if (Notification.permission === 'granted') {
      const sw = await navigator.serviceWorker.ready;
      const sub = await sw.pushManager.getSubscription();
      if (sub) updatePushBtn(true);
    }
  }

  async function togglePush() {
    if (!('Notification' in window) || !('PushManager' in window)) { showToast('Push not supported'); return; }
    try {
      const sw = await navigator.serviceWorker.ready;
      const existing = await sw.pushManager.getSubscription();
      if (existing) {
        await existing.unsubscribe();
        await fetch('/api/push/unsubscribe', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint: existing.endpoint }) });
        updatePushBtn(false);
        showToast('Notifications off');
        return;
      }
      const perm = await Notification.requestPermission();
      if (perm !== 'granted') { showToast('Notifications blocked. Allow them in browser settings.'); return; }
      const sub = await sw.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY) });
      const res = await fetch('/api/push/subscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ subscription: sub.toJSON() }) });
      if (!res.ok) { await sub.unsubscribe().catch(() => {}); throw new Error('subscribe ' + res.status); }
      updatePushBtn(true);
      showToast('Notifications on');
    } catch (e) {
      console.warn('[push]', e);
      showToast('Could not update notifications. Try again.');
    }
  }

  window.addEventListener('load', initPush);
  document.getElementById('pushBtn')?.addEventListener('click', togglePush);

  // ── APPLE WALLET ──────────────────────────────────────────────────────
  // A .pkpass only does something on Apple devices; elsewhere the badge stays
  // hidden and Save Contact spans the row.
  const ua = navigator.userAgent;
  const isApple = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && /Safari/.test(ua) && !/Chrome|CriOS|FxiOS|Edg/.test(ua));
  const wallet = document.getElementById('walletBtn');
  // Removed (not just hidden) elsewhere, so the odd-cell rule lets Save Contact span the row.
  if (wallet) { if (isApple) wallet.hidden = false; else wallet.remove(); }

  // ── SIGNAL / WHATSAPP ─────────────────────────────────────────────────
  // First press reveals; the button then becomes a real link, so it can be
  // long-pressed, copied or opened in a new tab, and opens with noopener.
  function reveal(btn, href, text, label, service) {
    const a = document.createElement('a');
    a.className = 'link-row';
    a.href = href;
    a.target = '_blank';
    a.rel = 'noopener';
    a.setAttribute('aria-label', label);
    a.innerHTML = btn.innerHTML;
    const val = a.querySelector('.link-val');
    val.textContent = text;
    val.classList.remove('redacted');
    val.classList.add('revealed');
    a.querySelector('.link-arr').classList.add('live');
    btn.replaceWith(a);
    a.focus();
    showToast(service + ' shown. Press again to open.');
  }

  document.getElementById('signal-btn')?.addEventListener('click', function () {
    reveal(this, 'https://signal.me/#eu/pipiM-n90HDfbE-rD_MVM1L8g3JJA-BXcmffyBAaFq7K1pg95_JMaJLfXqOm2jNi',
      '@special.123', 'Open Signal, @special.123', 'Signal');
  });
  document.getElementById('wa-btn')?.addEventListener('click', function () {
    reveal(this, 'https://wa.me/12123086406', 'Open chat', 'Open WhatsApp', 'WhatsApp');
  });

  // ── SHARE / COPY ──────────────────────────────────────────────────────
  function copyLink() {
    navigator.clipboard.writeText('https://contact.jamestannahill.com')
      .then(() => showToast('Link copied'))
      .catch(() => showToast('Unable to copy. Use Share QR instead.'));
  }

  async function shareQR() {
    const canvas = document.getElementById('qr');
    try {
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      const file = new File([blob], 'james-tannahill-contact.png', { type: 'image/png' });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ title: 'James Tannahill: Contact', text: 'Scan to add contact', files: [file] });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'james-tannahill-qr.png'; a.click();
        // Revoking synchronously can cancel the download in Safari and Firefox.
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        showToast('QR downloaded');
      }
    } catch (e) {
      if (e.name !== 'AbortError') copyLink();
    }
  }

  document.getElementById('shareQrBtn')?.addEventListener('click', shareQR);
  document.getElementById('copyLinkBtn')?.addEventListener('click', copyLink);
  document.getElementById('saveContact')?.addEventListener('click', () => showToast('Contact card downloaded'));

  // ── QR ────────────────────────────────────────────────────────────────
  const MECARD = 'MECARD:N:Tannahill,James;ORG:SpaceXAI;TITLE:AI/ML for Capital Markets;EMAIL:contact@jamestannahill.com;URL:https://jamestannahill.com;ADR:W 57th Street\\, New York\\, NY;NOTE:Signal preferred;;';

  // Draw on whole device pixels: each module is an integer number of
  // physical pixels and the CSS size matches the bitmap exactly, so the
  // browser never resamples the code into a blur.
  function drawQR(canvas, targetCss, bg, decorate) {
    const qr = qrcode(0, 'L');
    qr.addData(MECARD);
    qr.make();
    const mc = qr.getModuleCount();
    const dpr = Math.max(1, Math.round(window.devicePixelRatio || 1));
    const quiet = 4;
    const cell = Math.max(1, Math.floor((targetCss * dpr) / (mc + quiet * 2)));
    const px = cell * (mc + quiet * 2);
    canvas.width = px; canvas.height = px;
    canvas.style.width = (px / dpr) + 'px';
    canvas.style.height = (px / dpr) + 'px';
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, px, px);
    ctx.fillStyle = '#1a1a1a';
    const m = quiet * cell;
    for (let r = 0; r < mc; r++) {
      for (let c = 0; c < mc; c++) {
        if (qr.isDark(r, c)) ctx.fillRect(c * cell + m, r * cell + m, cell, cell);
      }
    }
    if (decorate) {
      // Red crosshairs and corner ticks, drawn only in the quiet zone.
      const s = px, cx = s / 2, k = dpr;
      ctx.strokeStyle = 'rgba(224, 26, 26, 0.25)';
      ctx.lineWidth = 0.5 * k;
      [[0, cx, m - 6 * k, cx], [s - m + 6 * k, cx, s, cx], [cx, 0, cx, m - 6 * k], [cx, s - m + 6 * k, cx, s]]
        .forEach(([x1, y1, x2, y2]) => { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); });
      ctx.strokeStyle = 'rgba(224, 26, 26, 0.35)';
      ctx.lineWidth = k;
      const tm = 8 * k, o = m - 2 * k;
      [[o, o, 1, 1], [s - o, o, -1, 1], [o, s - o, 1, -1], [s - o, s - o, -1, -1]].forEach(([x, y, dx, dy]) => {
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + dx * tm, y); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + dy * tm); ctx.stroke();
      });
    }
  }

  let qrReturnFocus = null;
  let qrWakeLock = null;
  const overlay = document.getElementById('qrOverlay');
  const behind = [document.getElementById('main-content'), document.querySelector('.bb-topbar')];

  function requestWakeLock() {
    if (!('wakeLock' in navigator)) return;
    navigator.wakeLock.request('screen').then(l => { qrWakeLock = l; }).catch(() => {});
  }

  function openQROverlay(e) {
    if (e) e.stopPropagation();
    if (typeof qrcode === 'undefined') { showToast('QR unavailable. Use Save Contact.'); return; }
    qrReturnFocus = document.activeElement;
    drawQR(document.getElementById('qrLarge'), Math.min(260, window.innerWidth * 0.8), '#ffffff', false);
    // The page behind the dialog leaves the tab order and the accessibility tree.
    behind.forEach(el => { if (el) el.inert = true; });
    overlay.classList.add('active');
    overlay.removeAttribute('inert');
    overlay.setAttribute('aria-hidden', 'false');
    document.getElementById('qrClose').focus();
    requestWakeLock();
  }

  function closeQROverlay() {
    if (!overlay.classList.contains('active')) return;
    overlay.classList.remove('active');
    overlay.setAttribute('inert', '');
    overlay.setAttribute('aria-hidden', 'true');
    behind.forEach(el => { if (el) el.inert = false; });
    if (qrWakeLock) { qrWakeLock.release().catch(() => {}); qrWakeLock = null; }
    if (qrReturnFocus && qrReturnFocus.focus) qrReturnFocus.focus();
  }

  // The browser drops the wake lock when the tab is hidden; take it back.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && overlay.classList.contains('active')) requestWakeLock();
  });

  overlay.addEventListener('click', closeQROverlay);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeQROverlay(); });
  document.getElementById('qrTopBtn')?.addEventListener('click', openQROverlay);

  const qrCanvas = document.getElementById('qr');
  if (qrCanvas) {
    qrCanvas.addEventListener('click', openQROverlay);
    qrCanvas.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openQROverlay(e); }
    });
  }

  (function loadQR() {
    if (!qrCanvas) return;
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js';
    script.integrity = 'sha384-lQXOAyZwHXE55JFyrOMB7nY2Wv+m5ZWNtJcHrd1rceRQXAYNLak8ukN5TjBTcIwz';
    script.crossOrigin = 'anonymous';
    script.onload = () => drawQR(qrCanvas, Math.min(188, window.innerWidth * 0.62), '#f8f8f8', true);
    script.onerror = () => {
      qrCanvas.width = 160; qrCanvas.height = 160;
      const ctx = qrCanvas.getContext('2d');
      ctx.fillStyle = '#f8f8f8'; ctx.fillRect(0, 0, 160, 160);
      ctx.fillStyle = '#6b6b6b'; ctx.font = '11px JetBrains Mono, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('QR unavailable', 80, 74);
      ctx.fillText('Use Save Contact', 80, 88);
    };
    document.head.appendChild(script);
  })();

  // ── SCROLL REVEAL ─────────────────────────────────────────────────────
  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll('.sr').forEach(el => obs.observe(el));
  } else {
    document.querySelectorAll('.sr').forEach(el => el.classList.add('visible'));
  }
  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('.sr').forEach(el => el.classList.add('visible'));
  });
})();
