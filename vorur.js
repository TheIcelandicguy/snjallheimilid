'use strict';
/* The product page (vorur.html, written by tools/products.py). Without this script every card shows and the filters are hidden. With it: a tick in
   a group keeps the cards that match any tick of that group, and every group at once; the number beside a choice says how many cards it would
   show with the other groups as they stand; a colour picked shows each picture in that colour; the choices are kept in the address, so a filtered
   list can be sent on as a link. */
(() => {
  const lang = document.documentElement.lang || 'is', base = lang === 'is' ? '' : '../';
  document.getElementById('year').textContent = String(new Date().getFullYear());
  document.querySelectorAll('[data-aetlun]').forEach((a) => { a.href = a.href.split('?')[0] + (lang === 'is' ? '' : '?lang=' + lang); });
  document.querySelectorAll('.lang a').forEach((a) => { if (a.getAttribute('lang') === lang) a.setAttribute('aria-current', 'page'); });

  const pv = document.querySelector('.pv'), form = document.getElementById('pvFilters');
  if (!pv || !form) return;
  const cards = [...document.querySelectorAll('.pv-card')].map((el) => ({ el, img: el.querySelector('img'), line: el.dataset.line, cat: el.dataset.cat, smart: el.dataset.smart, fits: el.dataset.fits.split(' ') }));
  const boxes = [...form.querySelectorAll('input[type=checkbox]')], groups = ['line', 'fit', 'cat', 'smart'];
  const count = document.getElementById('pvCount'), none = document.getElementById('pvNone'), clear = document.getElementById('pvClear');
  const toggle = document.getElementById('pvToggle'), on = document.getElementById('pvOn');

  const picked = () => Object.fromEntries(groups.map((g) => [g, boxes.filter((b) => b.name === g && b.checked).map((b) => b.value)]));
  // does a card pass one group's ticks (no tick = everything passes)
  const pass = (c, g, vals) => !vals.length || (g === 'fit' ? vals.some((v) => c.fits.includes(v)) : vals.includes(c[g]));
  const show = () => {
    const p = picked();
    let n = 0;
    for (const c of cards) {
      const ok = groups.every((g) => pass(c, g, p[g]));
      c.el.hidden = !ok;
      if (!ok) continue;
      n++;
      // the picture in the first colour picked that the part is made in, else in its own first colour
      const fit = p.fit.find((f) => c.fits.includes(f)) || c.fits[0], src = `${base}img/lines3d/${c.line}-${fit}-${c.img.dataset.file}.webp`;
      if (c.img.getAttribute('src') !== src) c.img.src = src;
    }
    // beside each choice: how many cards it shows with the other groups as they stand
    for (const b of boxes) {
      const k = cards.filter((c) => groups.every((g) => (g === b.name ? pass(c, g, [b.value]) : pass(c, g, p[g])))).length;
      b.parentElement.querySelector('[data-n]').textContent = `(${k})`;
      b.parentElement.classList.toggle('zero', !k && !b.checked);
      b.disabled = !k && !b.checked;
    }
    const ticks = boxes.filter((b) => b.checked).length;
    count.textContent = String(n);
    none.hidden = n > 0;
    clear.hidden = !ticks;
    on.textContent = ticks ? ` (${ticks})` : '';
    const q = groups.filter((g) => p[g].length).map((g) => `${g}=${p[g].join(',')}`).join('&');
    history.replaceState(null, '', location.pathname + (q ? '?' + q : ''));
  };

  // the choices of the address this page was opened with
  const q = new URLSearchParams(location.search);
  for (const b of boxes) b.checked = (q.get(b.name) || '').split(',').includes(b.value);
  pv.classList.add('js');
  form.addEventListener('change', show);
  form.addEventListener('submit', (e) => e.preventDefault());
  clear.addEventListener('click', () => { boxes.forEach((b) => { b.checked = false; }); show(); });
  toggle.addEventListener('click', () => { const open = toggle.getAttribute('aria-expanded') !== 'true'; toggle.setAttribute('aria-expanded', String(open)); pv.classList.toggle('filters-open', open); });
  show();
})();
