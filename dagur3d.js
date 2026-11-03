/* Einn dagur in 3D (owner 2026-11-03, "meira 3D"): the scene player's house built with Three.js over the drawing.
   The plan drawing of the SVG player (.dsvg, its house group) is painted on the floor as a texture, the walls rise
   from it as half-transparent slabs with their edges drawn, every ceiling light is a glow sprite plus a point light
   that pools on the drawing, and the camera flies to each scene. site.js still runs the scenes: this file watches
   data-scene on .dagur and animates what the scene asks for (lights going off in turn, the door opening, the energy
   bars, the curtain, the water rings, the labels). Without WebGL, with prefers-reduced-motion, or if Three.js does
   not load, the SVG player stays as it is. Plan px -> metres: 0.01 (the sample house is 6.0 x 4.4 m). */
import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.min.js';

const root = document.querySelector('.dagur'), svg = root && root.querySelector('.dsvg');
if (root && svg && !matchMedia('(prefers-reduced-motion: reduce)').matches) init();

function init() {
  const S = 0.01, H = 2.5, DOOR = 2.1, SILL = 0.9;
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const box = document.createElement('div'); box.className = 'd3';
  const labels = document.createElement('div'); labels.className = 'd3labels'; box.appendChild(labels);
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false }); } catch (e) { return; }
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = false;
  box.insertBefore(renderer.domElement, labels);
  svg.parentNode.insertBefore(box, svg);
  svg.classList.add('d3off');

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 600 / 440, 0.1, 60);
  const accent = new THREE.Color(css('--accent') || '#f5a524');

  // ---- the floor: the drawing itself, rendered from the SVG with its styles inlined ----
  const floorMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0 });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(6, 4.4), floorMat);
  floor.rotation.x = -Math.PI / 2; floor.position.set(3, 0, 2.2); scene.add(floor);
  (function paintFloor() {
    const clone = svg.cloneNode(true);
    const src = svg.querySelectorAll('*'), dst = clone.querySelectorAll('*');
    src.forEach((el, i) => {
      const cs = getComputedStyle(el), d = dst[i];
      ['stroke', 'fill', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'font-size', 'font-family', 'font-weight', 'text-anchor'].forEach((p) => {
        const v = cs.getPropertyValue(p); if (v) d.style.setProperty(p, v);
      });
      d.style.opacity = el.classList.contains('glow') ? '0' : '1';
    });
    clone.querySelectorAll('.sc').forEach((g) => g.remove());
    clone.querySelectorAll('[id]').forEach((el) => el.removeAttribute('id'));
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); clone.setAttribute('width', '1200'); clone.setAttribute('height', '880');
    const bg = css('--card') || '#fff';
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = 1200; c.height = 880;
      const g = c.getContext('2d'); g.fillStyle = bg; g.fillRect(0, 0, 1200, 880); g.drawImage(img, 0, 0, 1200, 880);
      floorMat.map = new THREE.CanvasTexture(c); floorMat.map.colorSpace = THREE.SRGBColorSpace; floorMat.needsUpdate = true;
    };
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(clone));
  })();

  // ---- walls: segments split at the openings ----
  const wallMat = new THREE.MeshStandardMaterial({ color: 0xd6dbe1, transparent: true, opacity: 0.32, roughness: 0.9, depthWrite: false });
  const edgeMat = new THREE.LineBasicMaterial({ color: new THREE.Color(css('--text') || '#ddd'), transparent: true, opacity: 0.7 });
  function slab(x1, z1, x2, z2, t, y0, y1) {
    const len = Math.hypot(x2 - x1, z2 - z1), g = new THREE.BoxGeometry(len, y1 - y0, t);
    const m = new THREE.Mesh(g, wallMat); m.position.set((x1 + x2) / 2, (y0 + y1) / 2, (z1 + z2) / 2); m.rotation.y = -Math.atan2(z2 - z1, x2 - x1);
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(g), edgeMat); m.add(e); scene.add(m); return m;
  }
  // a wall from a to b (plan px) with openings [[from, to, kind]] along it
  function wall(ax, az, bx, bz, t, ops) {
    const horiz = az === bz, a = horiz ? ax : az, b = horiz ? bx : bz, fixed = horiz ? az : ax;
    const pt = (v) => horiz ? [v * S, fixed * S] : [fixed * S, v * S];
    let cur = Math.min(a, b); const end = Math.max(a, b);
    for (const [o1, o2, kind] of ops.sort((p, q) => p[0] - q[0])) {
      if (o1 > cur) slab(...pt(cur), ...pt(o1), t, 0, H);
      if (kind === 'win') { slab(...pt(o1), ...pt(o2), t, 0, SILL); slab(...pt(o1), ...pt(o2), t, DOOR, H); }
      else slab(...pt(o1), ...pt(o2), t, DOOR, H);
      cur = o2;
    }
    if (cur < end) slab(...pt(cur), ...pt(end), t, 0, H);
  }
  wall(30, 30, 570, 30, 0.2, [[80, 160, 'win'], [300, 370, 'win'], [440, 520, 'win']]);
  wall(30, 410, 570, 410, 0.2, [[180, 230, 'door']]);
  wall(30, 30, 30, 410, 0.2, [[100, 180, 'win']]);
  wall(570, 30, 570, 410, 0.2, [[260, 340, 'win']]);
  wall(250, 30, 250, 260, 0.1, []);
  wall(30, 260, 400, 260, 0.1, [[120, 170, 'door'], [300, 350, 'door']]);
  wall(400, 30, 400, 410, 0.1, [[80, 130, 'door'], [300, 350, 'door']]);
  wall(400, 200, 570, 200, 0.1, []);
  // the front door leaf, hinged at x = 1.8
  const door = new THREE.Group(); door.position.set(1.8, 0, 4.1); scene.add(door);
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(0.5, DOOR, 0.05), new THREE.MeshStandardMaterial({ color: 0xb08a5a, roughness: 0.8 }));
  leaf.position.set(0.25, DOOR / 2, 0); door.add(leaf);

  // ---- light ----
  scene.add(new THREE.AmbientLight(0xffffff, 0.35));
  const sun = new THREE.DirectionalLight(0xffffff, 0.6); sun.position.set(-4, 6, 2); scene.add(sun);
  const glowTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
    const r = g.createRadialGradient(64, 64, 0, 64, 64, 64); r.addColorStop(0, 'rgba(255,220,150,1)'); r.addColorStop(0.3, 'rgba(255,200,110,.6)'); r.addColorStop(1, 'rgba(255,180,80,0)');
    g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c);
  })();
  const LIGHTS = { stofa: [140, 145], eldhus: [325, 145], herbergi: [485, 115], bad: [485, 305], forstofa: [215, 335] };
  const lamps = {};
  for (const k in LIGHTS) {
    const [px, pz] = LIGHTS[k], x = px * S, z = pz * S;
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    sp.position.set(x, H - 0.12, z); scene.add(sp);
    const pl = new THREE.PointLight(0xffd28a, 0, 5, 1.4); pl.position.set(x, H - 0.3, z); scene.add(pl);
    lamps[k] = { sp, pl, level: 0, target: 0 };
  }
  // the under-cabinet strip in Eldhús: a thin bar that glows
  const stripMat = new THREE.MeshBasicMaterial({ color: 0xffd28a, transparent: true, opacity: 0 });
  const strip = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.03, 1.8), stripMat); strip.position.set(3.86, 1.35, 1.5); scene.add(strip);
  const stripL = new THREE.PointLight(0xffd28a, 0, 2.5, 1.8); stripL.position.set(3.75, 1.2, 1.5); scene.add(stripL);
  lamps.strip = { sp: strip, pl: stripL, level: 0, target: 0, bar: true };

  // ---- scene props ----
  const bars = [], BARS = [3, 5, 4, 22, 12, 6, 5, 4, 4, 5, 9, 26, 34, 18, 8];
  const barMat = new THREE.MeshStandardMaterial({ color: accent, emissive: accent, emissiveIntensity: 0.35, roughness: 0.6 });
  BARS.forEach((h, i) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.09, 1, 0.09), barMat); m.position.set(1.1 + i * 0.15, 0, 3.4); m.scale.y = 0.001; scene.add(m); bars.push([m, h / 34]);
  });
  const curtain = new THREE.Mesh(new THREE.PlaneGeometry(0.8, DOOR - SILL), new THREE.MeshStandardMaterial({ color: 0x8a7f72, side: THREE.DoubleSide, roughness: 1 }));
  curtain.position.set(0.42, (DOOR + SILL) / 2, 1.0); curtain.rotation.y = Math.PI / 2; curtain.scale.x = 0.001; curtain.geometry.translate(0.4, 0, 0); scene.add(curtain);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x4aa3ff, transparent: true, opacity: 0, side: THREE.DoubleSide });
  const rings = [0, 1].map(() => { const r = new THREE.Mesh(new THREE.RingGeometry(0.16, 0.2, 48), ringMat.clone()); r.rotation.x = -Math.PI / 2; r.position.set(5.26, 0.02, 3.82); scene.add(r); return r; });

  // ---- scenes: light levels, camera, sky, labels, animation per scene ----
  const CAM = {
    1: [[8.4, 4.2, -0.4], [4.7, 0.5, 2.0]], 2: [[3.4, 4.4, 5.8], [3.2, 0.4, 1.5]], 3: [[1.6, 3.8, 8.4], [2.3, 0.4, 3.3]],
    4: [[-2.0, 3.6, 6.6], [1.4, 0.4, 3.2]], 5: [[-3.0, 3.6, 4.4], [1.6, 0.5, 1.5]], 6: [[8.6, 3.8, 6.4], [4.7, 0.2, 3.0]], 7: [[3.0, 8.0, 6.2], [3.0, 0, 2.0]],
  };
  const LEVEL = { 1: { bad: .15, strip: .15 }, 2: { eldhus: .6, strip: 1, stofa: .5, bad: .5, forstofa: .5 }, 3: { eldhus: .6, strip: 1, stofa: .5, bad: .5, forstofa: .5, herbergi: .5 },
    4: {}, 5: { stofa: .7, eldhus: .35, forstofa: .3 }, 6: { forstofa: .12 }, 7: { stofa: .4, eldhus: .4, herbergi: .4, bad: .4, forstofa: .4 } };
  const SKY = { 1: '#0b1020', 2: '#2b3554', 3: '#a9c3da', 4: '#c3d6e6', 5: '#5a3b45', 6: '#090e1c', 7: '#171c28' };
  const SUN = { 1: [0.05, '#8fa0ff'], 2: [0.3, '#ffd9b0'], 3: [0.9, '#ffffff'], 4: [1.0, '#ffffff'], 5: [0.5, '#ff9a4a'], 6: [0.05, '#8fa0ff'], 7: [0.4, '#ffffff'] };
  const OFF = ['herbergi', 'bad', 'eldhus', 'strip', 'stofa', 'forstofa'];
  const LABELS = {
    1: [[[4.85, 1.6, 0.95], '04:50', 'bub', 0.2], [[4.85, 2.2, 3.05], '10 %', 'tag', 0.8], [[3.75, 1.5, 1.5], '10 %', 'tag', 1.0]],
    2: [[[3.25, 2.2, 1.45], '60 %', 'tag', 1.2], [[3.7, 1.3, 2.5], 'haldið inni = dimmað', 'bub', 0.4]],
    3: [[[2.0, 1.9, 3.9], 'Allt af', 'bub', 0.3], [[2.4, 1.4, 1.2], 'straujárn af', 'tag', 1.6]],
    4: [[[2.1, 1.3, 3.4], 'kWh í dag', 'tag', 0.5]],
    5: [[[0.5, 2.4, 1.4], 'gluggatjöld', 'tag', 1.2], [[1.4, 2.0, 1.45], 'kvöldstilling', 'tag', 0.6], [[4.2, 1.4, 3.0], '21 °C', 'bub', 0.9]],
    6: [[[2.15, 2.0, 3.35], '10 %', 'tag', 0.4], [[5.26, 1.2, 3.82], 'Vatn í baðherbergi', 'note', 1.2]],
    7: [],
  };
  let cur = 0, t0 = 0, camFrom, camTo, lookFrom, lookTo, skyFrom = new THREE.Color(SKY[1]), skyTo = skyFrom.clone(), sunTo = new THREE.Color('#fff'), sunI = 0;
  scene.background = skyFrom.clone(); scene.fog = new THREE.Fog(skyFrom.clone(), 9, 18);
  const look = new THREE.Vector3(3, 0.8, 2.2);
  const setScene = (n) => {
    if (n === cur) return;
    cur = n; t0 = performance.now();
    camFrom = camera.position.clone(); camTo = new THREE.Vector3(...CAM[n][0]); lookFrom = look.clone(); lookTo = new THREE.Vector3(...CAM[n][1]);
    skyFrom = scene.background.clone(); skyTo = new THREE.Color(SKY[n]); sunTo = new THREE.Color(SUN[n][1]); sunI = SUN[n][0];
    for (const k in lamps) lamps[k].target = LEVEL[n][k] || 0;
    labels.innerHTML = '';
    for (const [p, text, cls, delay] of LABELS[n]) { const d = document.createElement('div'); d.className = 'lab ' + cls; d.textContent = text; d.dataset.d = delay; d.dataset.p = p.join(','); labels.appendChild(d); }
    if (n === 7) { const d = document.createElement('div'); d.className = 'lab end'; d.innerHTML = '<b>Snjallheimilið</b>Allt á heimanetinu, engin áskrift.<span>Fáðu verðbil á 2 mínútum</span>'; d.dataset.d = 1.2; labels.appendChild(d); }
  };
  const first = Number(root.dataset.scene) || 1;
  camera.position.set(...CAM[first][0]); look.set(...CAM[first][1]); setScene(first);
  camera.position.copy(camTo); look.copy(lookTo); camFrom = camTo.clone(); lookFrom = lookTo.clone();
  new MutationObserver(() => setScene(Number(root.dataset.scene) || 1)).observe(root, { attributes: true, attributeFilter: ['data-scene'] });

  // ---- render loop ----
  const ease = (x) => x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x);
  let visible = true, w = 0, h = 0;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; }, { threshold: 0.05 }).observe(box);
  const v = new THREE.Vector3();
  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible || document.hidden) return;
    const cw = box.clientWidth, ch = Math.round(cw * 440 / 600);
    if (cw !== w || ch !== h) { w = cw; h = ch; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
    const t = (now - t0) / 1000, k = ease(t / 1.8);
    // the camera: fly, then drift a little
    const drift = Math.sin(now / 4000) * 0.12;
    camera.position.lerpVectors(camFrom, camTo, k); camera.position.x += drift;
    look.lerpVectors(lookFrom, lookTo, k); camera.lookAt(look);
    scene.background.lerpColors(skyFrom, skyTo, k); scene.fog.color.copy(scene.background);
    sun.color.lerp(sunTo, 0.05); sun.intensity += (sunI - sun.intensity) * 0.05;
    if (cur === 5) sun.position.set(-4, 6 - 4 * ease(t / 3), 2); else sun.position.set(-4, 6, 2);
    // lights: a target per scene, scene 3 turns them off one after another
    for (const k in lamps) {
      const L = lamps[k]; let target = L.target;
      if (cur === 3) target = t > 0.6 + OFF.indexOf(k) * 0.45 ? 0 : target;
      if (cur === 6 && k === 'forstofa') target = t > 3.2 ? 0 : target;
      L.level += (target - L.level) * 0.08;
      if (L.bar) { L.sp.material.opacity = Math.min(1, L.level * 1.5); L.pl.intensity = L.level * 6; }
      else { L.sp.material.opacity = Math.min(1, L.level * 1.6); L.sp.scale.setScalar(0.6 + L.level * 1.6); L.pl.intensity = L.level * 14; }
    }
    // the front door opens when leaving
    const dt = cur === 3 ? -1.1 * ease((t - 0.2) / 1.2) : 0; door.rotation.y += (dt - door.rotation.y) * 0.1;
    bars.forEach(([m, f], i) => { const s = cur === 4 ? f * ease((t - 0.4 - i * 0.07) / 0.6) : 0; m.scale.y = Math.max(0.001, s); m.position.y = m.scale.y / 2; });
    curtain.scale.x += ((cur === 5 ? ease((t - 0.8) / 1.4) : 0) - curtain.scale.x) * 0.1; if (curtain.scale.x < 0.001) curtain.scale.x = 0.001;
    rings.forEach((r, i) => { const p = cur === 6 ? ((t * 0.7 + i * 0.5) % 1) : 0; r.scale.setScalar(0.4 + p * 2.4); r.material.opacity = cur === 6 ? (1 - p) * 0.8 : 0; });
    // labels follow their point
    labels.querySelectorAll('.lab').forEach((d) => {
      d.style.opacity = t > Number(d.dataset.d) ? '1' : '0';
      if (!d.dataset.p) return;
      const [x, y, z] = d.dataset.p.split(',').map(Number); v.set(x, y, z).project(camera);
      d.style.left = ((v.x + 1) / 2 * 100) + '%'; d.style.top = ((1 - v.y) / 2 * 100) + '%';
    });
    renderer.render(scene, camera);
  }
  requestAnimationFrame(frame);
}
