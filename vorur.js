'use strict';
/* The product page (vorur.html, written by tools/products.py). Without this script every card shows, and the filters and the frame builder are hidden.
   The filters: a tick in a group keeps the cards that match any tick of that group, and every group at once; the number beside a choice says how
   many cards it would show with the other groups as they stand; a colour picked shows each picture in that colour.
   The frame builder: the plus on a card (or a drag) puts the part into a frame, which takes the line and the colour of its first part. Only parts of
   that line made in that colour go in, and the frame grows to the largest the line has in the colour. A position is pressed to move it or take it out.
   The filters and the frame are kept in the address, so both can be sent on as a link. */
(() => {
  const lang = document.documentElement.lang || 'is', base = lang === 'is' ? '' : '../';
  document.getElementById('year').textContent = String(new Date().getFullYear());
  document.querySelectorAll('[data-aetlun]').forEach((a) => { a.href = a.href.split('?')[0] + (lang === 'is' ? '' : '?lang=' + lang); });
  document.querySelectorAll('.lang a').forEach((a) => { if (a.getAttribute('lang') === lang) a.setAttribute('aria-current', 'page'); });

  const pv = document.querySelector('.pv'), form = document.getElementById('pvFilters');
  if (!pv || !form) return;
  const cards = [...document.querySelectorAll('.pv-card')].map((el) => ({ el, img: el.querySelector('img'), kind: el.querySelector('img').dataset.file, name: el.querySelector('h3').textContent,
    lineName: el.querySelector('.pv-line').textContent, line: el.dataset.line, cat: el.dataset.cat, smart: el.dataset.smart, fits: el.dataset.fits.split(' ') }));
  const boxes = [...form.querySelectorAll('input[type=checkbox]')], groups = ['line', 'fit', 'cat', 'smart'];
  const count = document.getElementById('pvCount'), none = document.getElementById('pvNone'), clear = document.getElementById('pvClear');
  const toggle = document.getElementById('pvToggle'), on = document.getElementById('pvOn');

  const picked = () => Object.fromEntries(groups.map((g) => [g, boxes.filter((b) => b.name === g && b.checked).map((b) => b.value)]));
  // does a card pass one group's ticks (no tick = everything passes)
  const pass = (c, g, vals) => !vals.length || (g === 'fit' ? vals.some((v) => c.fits.includes(v)) : vals.includes(c[g]));

  /* ---- the frame builder ---- */
  const pb = document.getElementById('pb'), data = JSON.parse(document.getElementById('pbData').textContent);
  const text = Object.fromEntries([...document.querySelectorAll('#pbText [data-t]')].map((s) => [s.dataset.t, s.textContent]));
  const frameEl = document.getElementById('pbFrame'), nameEl = document.getElementById('pbName'), msgEl = document.getElementById('pbMsg'), selEl = document.getElementById('pbSel');
  const fitBtns = [...document.querySelectorAll('.pb-fit')], fitName = Object.fromEntries(fitBtns.map((b) => [b.dataset.fit, b.title]));
  const box = { line: '', fit: 'white', slots: [], sel: -1 }; // slots: a kind of part or '' per position
  const cardOf = (line, kind) => cards.find((c) => c.line === line && c.kind === kind);
  const sizes = () => (data.sizes[box.line] || {})[box.fit] || [1];
  const say = (t) => { msgEl.textContent = t || ''; };
  // the colours of the line in which every part now in the frame is made
  const fitsNow = () => Object.keys(data.sizes[box.line] || {}).filter((f) => box.slots.every((k) => !k || cardOf(box.line, k).fits.includes(f)));

  const C = 60, PAD = 7, H = 74;
  const plate = (w) => {
    if (box.line !== 'mosaic') return `<rect class="plate" x="0.5" y="0.5" width="${w - 1}" height="${H - 1}"/><rect class="gloss" x="0.5" y="0.5" width="${w - 1}" height="${H - 1}"/>`;
    const a = 4, b = 11; // Mosaic's plate: the lower corners rounder than the upper
    return `<path class="plate" d="M${a} .5H${w - a}A${a} ${a} 0 0 1 ${w - 0.5} ${a}V${H - b}A${b} ${b} 0 0 1 ${w - b} ${H - 0.5}H${b}A${b} ${b} 0 0 1 .5 ${H - b}V${a}A${a} ${a} 0 0 1 ${a} .5Z"/><path class="band" d="M${a + 2} 5H${w - a - 2}"/>`;
  };
  const draw = () => {
    const has = !!box.line, n = box.slots.length;
    pb.classList.toggle('has', has);
    pb.dataset.line = box.line; pb.dataset.fit = box.fit;
    if (!has) { frameEl.innerHTML = ''; nameEl.textContent = ''; selEl.hidden = true; }
    else {
      const w = C * n + 2 * PAD;
      const cells = box.slots.map((k, i) => `<g transform="translate(${PAD + i * C} ${PAD - 6})">${k ? `<g class="cell">${data.glyphs[k]}</g>` : '<rect class="slot" x="6" y="12" width="48" height="48" rx="5"/>'}</g>`).join('');
      // the drawing, and over each position a button to press, drag and drop on
      frameEl.innerHTML = `<svg class="lv-svg" viewBox="0 0 ${w} ${H}" style="--n:${n}" aria-hidden="true">${plate(w)}${cells}</svg>`
        + box.slots.map((k, i) => `<button type="button" class="pb-slot${i === box.sel ? ' on' : ''}" data-i="${i}" style="left:${(PAD + i * C) / w * 100}%;width:${C / w * 100}%"${k ? ' draggable="true"' : ''} aria-pressed="${i === box.sel}"></button>`).join('');
      frameEl.querySelectorAll('.pb-slot').forEach((b, i) => b.setAttribute('aria-label', box.slots[i] ? cardOf(box.line, box.slots[i]).name : text.slot));
      const parts = box.slots.filter(Boolean).map((k) => cardOf(box.line, k).name);
      nameEl.textContent = `${cardOf(box.line, box.slots.find(Boolean)).lineName}, ${fitName[box.fit].toLowerCase()}: ${text['s' + n].toLowerCase()}` + (parts.length ? ' – ' + parts.join(' + ') : '');
      const can = fitsNow(), all = Object.keys(data.sizes[box.line]);
      document.getElementById('pbFits').hidden = all.length < 2;
      fitBtns.forEach((b) => { b.hidden = !all.includes(b.dataset.fit); b.disabled = !can.includes(b.dataset.fit); b.setAttribute('aria-pressed', String(b.dataset.fit === box.fit)); });
      document.getElementById('pbLess').disabled = n < 2 || !box.slots.includes('');
      document.getElementById('pbMore').disabled = n >= Math.max(...sizes());
      selEl.hidden = box.sel < 0;
      if (box.sel >= 0) { document.getElementById('pbLeft').disabled = box.sel === 0; document.getElementById('pbRight').disabled = box.sel === n - 1; }
    }
    // a card's plus is dimmed where the part cannot go into the frame as it stands
    for (const c of cards) c.add.classList.toggle('off', has && (c.line !== box.line || !c.fits.includes(box.fit)));
    sync();
  };
  const empty = () => { box.line = ''; box.slots = []; box.sel = -1; };
  // put a card's part into position i, or into the first empty one, growing the frame while the line has a larger one
  const put = (c, i) => {
    say('');
    if (!box.line) { box.line = c.line; box.fit = picked().fit.find((f) => c.fits.includes(f)) || c.fits[0]; box.slots = ['']; }
    if (c.line !== box.line) return say(text.line);
    if (!c.fits.includes(box.fit)) return say(text.fit);
    if (i === undefined) i = box.slots.indexOf('');
    if (i < 0) {
      if (box.slots.length >= Math.max(...sizes())) return say(text.full.replace('{n}', Math.max(...sizes())));
      i = box.slots.push('') - 1;
    }
    box.slots[i] = c.kind; box.sel = -1;
    draw();
  };
  const swap = (a, b) => { [box.slots[a], box.slots[b]] = [box.slots[b], box.slots[a]]; box.sel = -1; say(''); draw(); };

  for (const c of cards) {
    c.add = document.createElement('button');
    Object.assign(c.add, { type: 'button', className: 'pv-add', textContent: '+', title: text.add });
    c.add.setAttribute('aria-label', `${text.add}: ${c.name}`);
    c.el.querySelector('.pv-pic').append(c.add);
    c.add.addEventListener('click', () => put(c));
    c.el.draggable = true;
    c.el.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/plain', 'card:' + cards.indexOf(c)); e.dataTransfer.effectAllowed = 'copy'; pb.classList.add('drag'); });
    c.el.addEventListener('dragend', () => pb.classList.remove('drag'));
  }
  frameEl.addEventListener('click', (e) => {
    const b = e.target.closest('.pb-slot'); if (!b) return;
    const i = Number(b.dataset.i);
    say('');
    if (box.sel >= 0 && box.sel !== i) return swap(box.sel, i); // a pressed part goes to the position pressed next
    box.sel = box.slots[i] && box.sel !== i ? i : -1;
    draw();
  });
  frameEl.addEventListener('dragstart', (e) => { const b = e.target.closest('.pb-slot'); if (b) { e.dataTransfer.setData('text/plain', 'slot:' + b.dataset.i); e.dataTransfer.effectAllowed = 'move'; } });
  pb.addEventListener('dragover', (e) => { e.preventDefault(); });
  pb.addEventListener('drop', (e) => {
    e.preventDefault(); pb.classList.remove('drag');
    const [what, n] = (e.dataTransfer.getData('text/plain') || '').split(':'), b = e.target.closest('.pb-slot'), i = b ? Number(b.dataset.i) : undefined;
    if (what === 'card' && cards[n]) put(cards[n], i);
    else if (what === 'slot' && i !== undefined && i !== Number(n)) swap(Number(n), i);
  });
  document.getElementById('pbLess').addEventListener('click', () => { box.slots.splice(box.slots.lastIndexOf(''), 1); box.sel = -1; say(''); draw(); });
  document.getElementById('pbMore').addEventListener('click', () => { box.slots.push(''); say(''); draw(); });
  document.getElementById('pbLeft').addEventListener('click', () => { const i = box.sel; swap(i, i - 1); box.sel = i - 1; draw(); });
  document.getElementById('pbRight').addEventListener('click', () => { const i = box.sel; swap(i, i + 1); box.sel = i + 1; draw(); });
  document.getElementById('pbOut').addEventListener('click', () => { box.slots[box.sel] = ''; box.sel = -1; if (!box.slots.some(Boolean)) empty(); say(''); draw(); });
  document.getElementById('pbReset').addEventListener('click', () => { empty(); say(''); draw(); });
  fitBtns.forEach((b) => b.addEventListener('click', () => {
    box.fit = b.dataset.fit;
    const max = Math.max(...sizes()); // a colour whose largest frame is smaller: the empty positions go first
    while (box.slots.length > max && box.slots.includes('')) box.slots.splice(box.slots.lastIndexOf(''), 1);
    say(''); draw();
  }));

  /* ---- the filters ---- */
  const show = () => {
    const p = picked();
    let n = 0;
    for (const c of cards) {
      const ok = groups.every((g) => pass(c, g, p[g]));
      c.el.hidden = !ok;
      if (!ok) continue;
      n++;
      // the picture in the first colour picked that the part is made in, else in its own first colour
      const fit = p.fit.find((f) => c.fits.includes(f)) || c.fits[0], src = `${base}img/lines3d/${c.line}-${fit}-${c.kind}.webp`;
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
    sync();
  };
  // the address: the filters' ticks, and the frame as box=line:colour:part,part (an empty position is -)
  function sync() {
    const p = picked(), q = groups.filter((g) => p[g].length).map((g) => `${g}=${p[g].join(',')}`);
    if (box.line) q.push(`box=${box.line}:${box.fit}:${box.slots.map((k) => k || '-').join(',')}`);
    history.replaceState(null, '', location.pathname + (q.length ? '?' + q.join('&') : ''));
  }

  // the choices and the frame of the address this page was opened with; what does not fit the lists is left out
  const q = new URLSearchParams(location.search);
  for (const b of boxes) b.checked = (q.get(b.name) || '').split(',').includes(b.value);
  const [bl, bf, bs] = (q.get('box') || '').split(':');
  if (data.sizes[bl] && data.sizes[bl][bf] && bs) {
    const slots = bs.split(',').map((k) => (k === '-' ? '' : k)).slice(0, Math.max(...data.sizes[bl][bf]));
    if (slots.some(Boolean) && slots.every((k) => !k || (cardOf(bl, k) && cardOf(bl, k).fits.includes(bf)))) { box.line = bl; box.fit = bf; box.slots = slots; }
  }
  pv.classList.add('js');
  pb.hidden = false;
  form.addEventListener('change', show);
  form.addEventListener('submit', (e) => e.preventDefault());
  clear.addEventListener('click', () => { boxes.forEach((b) => { b.checked = false; }); show(); });
  toggle.addEventListener('click', () => { const open = toggle.getAttribute('aria-expanded') !== 'true'; toggle.setAttribute('aria-expanded', String(open)); pv.classList.toggle('filters-open', open); });
  // the builder stays in sight under the page's header while it holds a frame; the filters beside the cards start under it
  const head = document.querySelector('header.top'), place = () => { pv.style.setProperty('--top', head.offsetHeight + 'px'); pv.style.setProperty('--pbh', (pb.classList.contains('has') ? pb.offsetHeight : 0) + 'px'); };
  if ('ResizeObserver' in window) { const ro = new ResizeObserver(place); ro.observe(head); ro.observe(pb); }
  addEventListener('resize', place);
  draw(); show(); place();
})();
