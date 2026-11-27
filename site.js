'use strict';
/* Snjallheimilið: the home page's small script. The estimate lives in the smart-home-estimator repo (quick.html);
   AETLUN is its address, every [data-aetlun] link points there (aetlun.snjallheimilid.is since 2026-11-02); the markup
   carries the same address, so the links work without this script, and tools/i18n.py writes ?lang= into the copies.
   The contact form posts JSON to Formspree (same form as the estimate page, another subject). */
const AETLUN = 'https://aetlun.snjallheimilid.is/quick.html';
const FORM = 'mjyypvge';
// the page's language: tools/i18n.py writes en/, es/ and pl/ copies of index.html and puts the few strings this script
// shows into them as JSON (#i18n, data and not script: the page's Content-Security-Policy runs no script written in the
// page); Icelandic is the source and needs no table
const I18N = JSON.parse((document.getElementById('i18n') || {}).textContent || 'null');
const LANG = (I18N && I18N.lang) || 'is';
const t = (s) => (I18N && I18N.t[s]) || s;
const base = LANG === 'is' ? '' : '../';

document.querySelectorAll('[data-aetlun]').forEach((a) => { a.href = AETLUN + (LANG === 'is' ? '' : '?lang=' + LANG); });
document.querySelectorAll('.lang a').forEach((a) => { if (a.getAttribute('lang') === LANG) a.setAttribute('aria-current', 'page'); });
document.getElementById('year').textContent = String(new Date().getFullYear());

// without this script the form posts itself to Formspree (method and action in the markup) and the browser checks the fields;
// with it the answer is shown here, so the browser's own check is switched off and the fields are checked below
const MAIL = 'david@snjallheimilid.is';
const form = document.getElementById('contact'), msg = document.getElementById('formMsg');
form.noValidate = true;
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target, say = (t, cls) => { msg.textContent = t; msg.className = 'fine ' + cls; };
  if (!f.name.value.trim() || !f.email.value.trim() || !f.message.value.trim() || !f.email.checkValidity()) return say(t('Nafn, netfang og erindi þarf að fylla út.'), 'err');
  if (f._gotcha.value) return; // a bot filled the hidden field
  const btn = f.querySelector('button[type=submit]'); btn.disabled = true; say(t('Sendi…'), '');
  const data = { name: f.name.value, email: f.email.value, phone: f.phone.value, place: f.place.value, message: f.message.value, _subject: t('Fyrirspurn af snjallheimilid.is'), lang: LANG };
  try {
    const r = await fetch(`https://formspree.io/f/${FORM}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(data) });
    if (!r.ok) throw new Error('svar ' + r.status);
    f.reset(); say(t('Takk, erindið er komið. Ég svara eins fljótt og ég get.'), 'ok');
  } catch (err) {
    // the address stands in the message as a link: the text around it is set as text, never as HTML
    const [a, b] = t('Sending tókst ekki ({err}). Reyndu aftur, eða sendu póst beint á {mail}.').replace('{err}', err.message).split('{mail}');
    const link = document.createElement('a'); link.href = 'mailto:' + MAIL; link.textContent = MAIL;
    say(a, 'err'); msg.append(link, b || ''); btn.disabled = false;
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
  fetch(base + 'tools/film/timeline' + (LANG === 'is' ? '' : '.' + LANG) + '.json').then((r) => r.json()).then((tl) => {
    const lines = tl.scenes.flatMap((s) => s.lines.map(([t, text]) => ({ t, title: s.title, text })));
    const say = () => {
      const now = v.currentTime < tl.end_card ? lines.filter((l) => v.currentTime >= l.t).pop() || lines[0] : null;
      line.hidden = !now;
      if (now) { line.children[0].textContent = now.title; line.children[1].textContent = now.text; }
    };
    v.addEventListener('timeupdate', say);
    say();
  }).catch(() => {});
  v.addEventListener('play', () => { play.textContent = t('Stöðva'); });
  v.addEventListener('pause', () => { play.textContent = t('Spila'); });
  dots.forEach((d) => d.addEventListener('click', () => { v.currentTime = Number(d.dataset.go); mark(); held = false; seen = true; v.play().catch(() => {}); }));
  play.addEventListener('click', () => { if (v.paused) { held = false; seen = true; v.play().catch(() => {}); } else { held = true; v.pause(); } });
  mark();
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((es) => { seen = es[0].isIntersecting; if (seen) go(); else v.pause(); }, { threshold: 0.35 }).observe(v);
  } else { seen = true; go(); }
})();

/* Vörur í boði: tabs (role tablist). Click or arrow keys / Home / End change the panel; without this script every panel shows. */
(() => {
  const box = document.querySelector('.vtabs');
  if (!box) return;
  const tabs = [...box.querySelectorAll('[role=tab]')], panels = tabs.map((b) => document.getElementById(b.getAttribute('aria-controls')));
  const show = (n, focus) => {
    tabs.forEach((b, i) => { b.setAttribute('aria-selected', i === n ? 'true' : 'false'); b.tabIndex = i === n ? 0 : -1; panels[i].classList.toggle('on', i === n); });
    if (focus) tabs[n].focus();
  };
  box.classList.add('js');
  tabs.forEach((b, i) => {
    b.addEventListener('click', () => show(i));
    b.addEventListener('keydown', (e) => {
      const k = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (k === undefined) return;
      e.preventDefault(); show((k + tabs.length) % tabs.length, true);
    });
  });
  show(0);
})();

// The drawn view of the fitting lines (owner 2026-11-24; the markup is written by tools/lines_view.py). Without this script every line's set shows, one
// under the other. With it: a tab shows one line, a round swatch paints the wall, BSEED's lines can be had in four colours, and the
// drawings can be swapped for the 3D pictures. The drawings themselves do nothing when pressed (owner 2026-11-25: leave the interactive part out).
(() => {
  const lv = document.querySelector('.lv');
  if (!lv) return;
  const wall = lv.querySelector('.lv-wall'), fits = lv.querySelector('.lv-fits');
  const press = (list, on) => list.forEach((b) => b.setAttribute('aria-pressed', b === on ? 'true' : 'false'));
  const dark = (hex) => { const n = parseInt(hex.slice(1), 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) < 140; };
  // the gloss of a glass frame, drawn once for every drawing to use
  wall.insertAdjacentHTML('afterbegin', '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><linearGradient id="lv-gloss" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".38"/><stop offset=".45" stop-color="#fff" stop-opacity=".04"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs></svg>');
  // the 3D pictures of the line and colour in hand, asked for only once the 3D view is chosen
  const pics = () => { if (lv.dataset.mode !== '3d') return; lv.querySelectorAll('.lv-set.on .lv-hero img[data-src]').forEach((im) => { im.src = base + im.dataset.src; im.removeAttribute('data-src'); }); lv.querySelectorAll('.lv-set.on .lv-fig:not([hidden]) .lv-pic').forEach((im) => { const src = `${base}img/lines3d/${lv.dataset.line}-${lv.dataset.fit}-${im.dataset.file}.webp`; if (im.getAttribute('src') !== src) im.src = src; }); };
  // a part that is not made in every colour of its line is shown with the colours it is made in
  const made = () => lv.querySelectorAll('.lv-fig[data-fits]').forEach((f) => { f.hidden = !f.dataset.fits.split(' ').includes(lv.dataset.fit); });
  const fit = (k) => { lv.dataset.fit = k; press([...lv.querySelectorAll('.lv-fit')], lv.querySelector(`.lv-fit[data-fit="${k}"]`)); made(); pics(); };
  const line = (tab) => {
    lv.dataset.line = tab.dataset.line;
    press([...lv.querySelectorAll('.lv-tab')], tab);
    lv.querySelectorAll('.lv-set').forEach((s) => s.classList.toggle('on', s.dataset.set === tab.dataset.line));
    const can = tab.dataset.fits.split(' ');
    fits.hidden = can.length < 2;
    if (!can.includes(lv.dataset.fit)) fit('white');
    pics();
  };
  lv.classList.add('js');
  line(lv.querySelector('.lv-tab'));
  lv.addEventListener('click', (e) => {
    const tab = e.target.closest('.lv-tab'), sw = e.target.closest('.lv-sw'), f = e.target.closest('.lv-fit'), mode = e.target.closest('.lv-mode');
    if (tab) line(tab);
    else if (mode) { lv.dataset.mode = mode.dataset.mode; press([...lv.querySelectorAll('.lv-mode')], mode); pics(); }
    else if (sw) { wall.style.setProperty('--wall', sw.dataset.wall); wall.classList.toggle('darkwall', dark(sw.dataset.wall)); press([...lv.querySelectorAll('.lv-sw')], sw); }
    else if (f) fit(f.dataset.fit);
  });
})();
