'use strict';
/* Snjallheimilið: the home page's small script. The estimate lives in the smart-home-estimator repo (quick.html);
   AETLUN is its address, every [data-aetlun] link points there (aetlun.snjallheimilið.is since 2026-11-02).
   The contact form posts JSON to Formspree (same form as the estimate page, another subject). */
const AETLUN = 'https://aetlun.xn--snjallheimili-gkb.is/quick.html';
const FORM = 'mjyypvge';

document.querySelectorAll('[data-aetlun]').forEach((a) => { a.href = AETLUN; });
document.getElementById('year').textContent = String(new Date().getFullYear());

const form = document.getElementById('contact'), msg = document.getElementById('formMsg');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target, say = (t, cls) => { msg.textContent = t; msg.className = 'fine ' + cls; };
  if (!f.name.value.trim() || !f.email.value.trim() || !f.message.value.trim()) return say('Nafn, netfang og erindi þarf að fylla út.', 'err');
  if (f._gotcha.value) return; // a bot filled the hidden field
  const btn = f.querySelector('button[type=submit]'); btn.disabled = true; say('Sendi…', '');
  const data = { name: f.name.value, email: f.email.value, phone: f.phone.value, place: f.place.value, message: f.message.value, _subject: 'Fyrirspurn af snjallheimilið.is' };
  try {
    const r = await fetch(`https://formspree.io/f/${FORM}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(data) });
    if (!r.ok) throw new Error('svar ' + r.status);
    f.reset(); say('Takk, erindið er komið. Ég svara eins fljótt og ég get.', 'ok');
  } catch (err) {
    say('Sending tókst ekki (' + err.message + '). Reyndu aftur, eða sendu póst beint.', 'err'); btn.disabled = false;
  }
});

/* Einn dagur: the scene player in #dagur. data-scene on .dagur drives the CSS; scenes advance every 4 s (the last
   holds 5 s) while the section is on screen, a dot jumps to a scene and the play button stops and starts the run. */
(() => {
  const el = document.querySelector('.dagur');
  if (!el) return;
  const caps = el.querySelectorAll('.dcap > div'), dots = el.querySelectorAll('[data-go]'), play = el.querySelector('[data-play]');
  const N = caps.length, HOLD = [0, 6500, 5000, 6000, 6000, 6000, 6000, 9000];
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let cur = 1, timer = null, running = false, visible = false;
  const show = (n) => {
    cur = n; el.dataset.scene = String(n);
    caps.forEach((c) => c.classList.toggle('on', c.dataset.s === String(n)));
    dots.forEach((d) => d.setAttribute('aria-current', d.dataset.go === String(n) ? 'true' : 'false'));
  };
  const tick = () => { timer = setTimeout(() => { show(cur % N + 1); tick(); }, HOLD[cur]); };
  const start = () => { if (running || still) return; running = true; play.textContent = 'Stöðva'; tick(); };
  const stop = () => { running = false; clearTimeout(timer); timer = null; play.textContent = 'Spila'; };
  dots.forEach((d) => d.addEventListener('click', () => { stop(); show(Number(d.dataset.go)); }));
  play.addEventListener('click', () => (running ? stop() : start()));
  show(1);
  if (still) { play.textContent = 'Spila'; }
  else if ('IntersectionObserver' in window) {
    new IntersectionObserver((es) => {
      visible = es[0].isIntersecting;
      if (visible && !timer && play.textContent === 'Stöðva') start();
      if (!visible && running) { clearTimeout(timer); timer = null; running = false; }
    }, { threshold: 0.35 }).observe(el);
  } else start();
})();
