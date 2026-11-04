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

/* Einn dagur: the film in #dagur. Plays muted while the section is on screen, a dot jumps to a scene's start in seconds
   (data-go) and the play button stops and starts it; once stopped by hand, or with reduced motion, it waits to be asked. */
(() => {
  const v = document.querySelector('.dagur video');
  if (!v) return;
  const dots = [...document.querySelectorAll('[data-go]')], play = document.querySelector('[data-play]');
  let held = matchMedia('(prefers-reduced-motion: reduce)').matches, seen = false;
  const go = () => { if (!held && seen) v.play().catch(() => {}); };
  const mark = () => {
    const i = dots.reduce((a, d, n) => (v.currentTime >= Number(d.dataset.go) ? n : a), 0);
    dots.forEach((d, n) => d.setAttribute('aria-current', n === i ? 'true' : 'false'));
  };
  v.addEventListener('timeupdate', mark);
  // on a phone the words in the picture are too small to read, so the same lines stand under it (site.css shows them)
  const line = document.querySelector('.dline');
  fetch('tools/film/timeline.json').then((r) => r.json()).then((tl) => {
    const lines = tl.scenes.flatMap((s) => s.lines.map(([t, text]) => ({ t, title: s.title, text })));
    const say = () => {
      const now = v.currentTime < tl.end_card ? lines.filter((l) => v.currentTime >= l.t).pop() || lines[0] : null;
      line.hidden = !now;
      if (now) { line.children[0].textContent = now.title; line.children[1].textContent = now.text; }
    };
    v.addEventListener('timeupdate', say);
    say();
  }).catch(() => {});
  v.addEventListener('play', () => { play.textContent = 'Stöðva'; });
  v.addEventListener('pause', () => { play.textContent = 'Spila'; });
  dots.forEach((d) => d.addEventListener('click', () => { v.currentTime = Number(d.dataset.go); mark(); held = false; seen = true; v.play().catch(() => {}); }));
  play.addEventListener('click', () => { if (v.paused) { held = false; seen = true; v.play().catch(() => {}); } else { held = true; v.pause(); } });
  mark();
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((es) => { seen = es[0].isIntersecting; if (seen) go(); else v.pause(); }, { threshold: 0.35 }).observe(v);
  } else { seen = true; go(); }
})();
