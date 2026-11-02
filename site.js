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
