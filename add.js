// /add (NFC tap page). Served from 'self'; no CSP hash needed.
(function () {
    const ua = navigator.userAgent;
    const isIOS = /iPhone|iPad|iPod/.test(ua);
    const isSafari = /Safari/.test(ua) && !/CriOS|Chrome|FxiOS|OPiOS|EdgiOS/.test(ua);
    const isAndroid = /Android/.test(ua);

    if (isIOS && isSafari) {
      // Safari on iOS: show the wallet button, then open the pass
      document.getElementById('walletBtn').style.display = 'flex';
      // Auto-trigger after brief delay so user sees the card
      setTimeout(() => {
        window.location.href = '/JamesTannahill.pkpass';
      }, 800);
    } else if (isIOS) {
      // Chrome / Firefox on iOS
      document.getElementById('safariPrompt').style.display = 'block';
    } else if (isAndroid) {
      document.getElementById('fallback').style.display = 'block';
    } else {
      // Desktop: a QR of this page, so an iPhone camera opens it in Safari.
      document.getElementById('desktop').style.display = 'block';
      drawDesktopQR();
    }

    function drawDesktopQR() {
      const canvas = document.getElementById('qr');
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js';
      script.integrity = 'sha384-lQXOAyZwHXE55JFyrOMB7nY2Wv+m5ZWNtJcHrd1rceRQXAYNLak8ukN5TjBTcIwz';
      script.crossOrigin = 'anonymous';
      script.onload = () => {
        const qr = qrcode(0, 'M');
        qr.addData('https://contact.jamestannahill.com/add');
        qr.make();
        // Whole device pixels per module, never scaled by CSS, so it stays sharp.
        const mc = qr.getModuleCount(), quiet = 4;
        const dpr = Math.max(1, Math.round(window.devicePixelRatio || 1));
        const cell = Math.max(1, Math.floor((160 * dpr) / (mc + quiet * 2)));
        const px = cell * (mc + quiet * 2);
        canvas.width = px; canvas.height = px;
        canvas.style.width = (px / dpr) + 'px';
        canvas.style.height = (px / dpr) + 'px';
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#D8D4CC'; ctx.fillRect(0, 0, px, px);
        ctx.fillStyle = '#060606';
        for (let r = 0; r < mc; r++) for (let c = 0; c < mc; c++) {
          if (qr.isDark(r, c)) ctx.fillRect((c + quiet) * cell, (r + quiet) * cell, cell, cell);
        }
      };
      // No library: drop the code and the scan line; the contact link remains.
      script.onerror = () => {
        canvas.parentElement.remove();
        document.querySelector('#desktop .message').remove();
      };
      document.head.appendChild(script);
    }
})();
