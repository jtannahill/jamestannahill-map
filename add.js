// /add (NFC tap page). Served from 'self'; no CSP hash needed.
(function () {
    const ua = navigator.userAgent;
    const isIOS = /iPhone|iPad|iPod/.test(ua);
    const isSafari = /Safari/.test(ua) && !/CriOS|Chrome|FxiOS|OPiOS|EdgiOS/.test(ua);
    const isAndroid = /Android/.test(ua);

    if (isIOS && isSafari) {
      // Safari on iOS: show the wallet button, then open the pass
      document.getElementById('walletBtn').style.display = 'flex';
      document.getElementById('hint').textContent = 'tap to add · updates automatically';
      // Auto-trigger after brief delay so user sees the card
      setTimeout(() => {
        window.location.href = '/JamesTannahill.pkpass';
      }, 800);
    } else if (isIOS) {
      // Chrome / Firefox on iOS
      document.getElementById('safariPrompt').style.display = 'block';
      document.getElementById('hint').textContent = 'ios · non-safari browser detected';
    } else {
      // Android / Desktop
      document.getElementById('fallback').style.display = 'block';
      document.getElementById('hint').textContent = isAndroid ? 'android · apple wallet not available' : 'desktop · scan on iphone';
    }
})();
