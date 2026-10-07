// map.jamestannahill.com behaviour. Served from 'self' so the CSP needs no hashes.
// The overlays wait for the map to land; a failed map lands them at once.
const land = () => document.body.classList.add('is-landing');
const noMap = () => { document.body.classList.add('no-map'); land(); };
setTimeout(land, 6000); // backstop
// iOS only applies :active when a touchstart listener is in the chain.
document.addEventListener('touchstart', () => {}, { passive: true });

if (typeof mapboxgl === 'undefined') noMap();
else mapboxgl.accessToken = 'pk.eyJ1IjoiamFtZXN0YW5uYWhpbGwiLCJhIjoiY21tb3Y1cm96MGNpcDJxcHFmZTdkam0wcyJ9.0nI0daKUj042FAsus87gXQ';

const PLOCAMIUM = [-73.9749, 40.7636]; // 9 W 57th St, New York (Google place pin)

const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
let map;
try {
  map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/dark-v11',
  center: [-74.02, 40.72],  // Start slightly offset
  zoom: 10.5,               // Start zoomed out
  pitch: 0,
  bearing: 0,
  antialias: true,
  attributionControl: false,
  logoPosition: 'bottom-right'
  });
} catch (err) {
  noMap();
}

if (map) {
// Before the first load, any style, token or network failure shows the
// Google Maps fallback. Mapbox puts the HTTP status on e.error.status;
// over HTTP/2 the message is often empty, so the status is what counts.
map.on('error', e => {
  const err = e.error || {};
  if (!map.loaded() && (err.status === 401 || err.status === 403 || err.status === 0 ||
      /style|token|fetch|network/i.test(String(err.message)))) {
    noMap();
  }
});
// A map that never loads (stalled connection) also falls back.
setTimeout(() => { if (!map.loaded()) noMap(); }, 10000);

map.addControl(new mapboxgl.AttributionControl({ compact: true }), 'bottom-right');
const attribBtn = document.querySelector('.mapboxgl-ctrl-attrib-button');
if (attribBtn) attribBtn.setAttribute('aria-label', 'Toggle map attribution');

// A touch before the fly-in starts cancels it; the user's gesture wins
let userTook = false;
map.once('touchstart', () => { userTook = true; });
map.once('mousedown', () => { userTook = true; });
map.once('wheel', () => { userTook = true; });


map.on('load', () => {
  document.getElementById('map').classList.add('loaded');

  // Centre the pin in the space above the card, not the whole viewport, so
  // on short screens it never lands under the name link.
  const card = document.querySelector('.card');
  const padding = { top: 80, bottom: (card ? card.offsetHeight : 0) + 48, left: 0, right: 0 };

  // Cinematic fly-in; the overlays enter when it lands.
  if (still) {
    map.jumpTo({ center: PLOCAMIUM, zoom: 15.5, bearing: -12, padding });
    land();
  } else setTimeout(() => {
    if (userTook) { land(); return; }
    map.once('moveend', land);
    map.flyTo({
      center: PLOCAMIUM,
      zoom: 15.5,
      pitch: 0,
      bearing: -12,
      padding,
      duration: 3500,
      curve: 1.4,
      easing: t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
    });
  }, 400);

  // Plocamium marker with logo placeholder
  const markerEl = document.createElement('div');
  markerEl.className = 'marker-container';
  markerEl.setAttribute('aria-label', 'Former Plocamium Holdings office, W 57th Street. Show details');
  markerEl.setAttribute('aria-expanded', 'false');
  markerEl.innerHTML = `
    <div class="marker-ping"></div>
    <div class="marker-logo">
      <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
        <text x="14" y="19" text-anchor="middle" font-family="NHG Display, Helvetica Neue, sans-serif" font-weight="500" font-size="16" fill="#C9A84C">P</text>
      </svg>
    </div>
  `;

  const popup = new mapboxgl.Popup({
    offset: 24,
    closeButton: true,
    closeOnClick: false,
    maxWidth: '240px'
  }).setHTML(`
    <div class="popup-inner">
      <div class="popup-logo" aria-hidden="true">P</div>
      <div class="popup-name">Plocamium Holdings</div>
      <div class="popup-loc">Former office</div>
      <div class="popup-addr">W 57th Street</div>
      <div class="popup-loc">New York, NY</div>
      <a href="https://www.plocamium.com" class="popup-link">plocamium.com <span class="cta-arrow popup-arrow" aria-hidden="true"></span></a>
    </div>
  `);

  const marker = new mapboxgl.Marker({ element: markerEl })
    .setLngLat(PLOCAMIUM)
    .setPopup(popup)
    .addTo(map);

  popup.on('open', () => {
    markerEl.setAttribute('aria-expanded', 'true');
    const close = popup.getElement().querySelector('.mapboxgl-popup-close-button');
    if (close) close.removeAttribute('aria-hidden');
  });
  // Closing with the x button would drop focus to <body>; return it to the pin.
  popup.on('close', () => {
    markerEl.setAttribute('aria-expanded', 'false');
    if (document.activeElement === document.body || !document.activeElement) markerEl.focus();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && popup.isOpen()) {
      popup.remove();
      markerEl.focus();
    }
  });
});
}
  
