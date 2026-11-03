/* Einn dagur in 3D (owner 2026-11-03, "meira 3D", then "svona 3D" with a furnished render as the reference): the scene
   player's house built with Three.js over a rendered floor. The floor is img/dagur-floor.jpg, a top-down furnished
   render of the sample house (generated in Canva on 2026-11-03, 1456 x 1088 px); the walls rise from it as
   half-transparent slabs placed over the render's own walls (HOUSE below, measured in the image's pixels), every
   ceiling light is a glow sprite plus a point light that pools on the floor, and the camera flies to each scene.
   site.js still runs the scenes: this file watches data-scene on .dagur and animates what the scene asks for (lights
   going off in turn, the door opening, the energy bars, the curtain, the water rings, the labels). If the floor image
   fails, the SVG drawing is painted on the floor instead; without WebGL, with prefers-reduced-motion, or if Three.js
   does not load, the SVG player stays as it is. Image px -> metres: the image is 6.0 m wide. */
import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.min.js';

// ---- the house, in pixels of the floor image ----
const HOUSE = {
  img: 'img/dagur-floor.jpg', w: 1456, h: 1088, widthM: 6.0,
  walls: [ // [x1, y1, x2, y2, thickness m, openings [[from, to, 'win'|'door'], ...] along the wall]
    [70, 55, 1420, 55, 0.2, [[255, 390, 'win'], [615, 735, 'win']]],
    [70, 965, 1420, 965, 0.2, [[555, 690, 'door']]],
    [70, 55, 70, 965, 0.2, []],
    [1420, 55, 1420, 965, 0.2, [[230, 430, 'win']]],
    [530, 55, 530, 615, 0.1, []],
    [915, 55, 915, 615, 0.1, []],
    [70, 615, 1420, 615, 0.1, [[390, 470, 'door'], [600, 680, 'door'], [935, 1020, 'door']]],
    [1080, 615, 1080, 965, 0.1, [[700, 790, 'door']]],
  ],
  frontDoor: { hinge: [555, 965], width: 135 },
  lights: { stofa: [300, 340], eldhus: [720, 340], herbergi: [1160, 340], bad: [1240, 790], forstofa: [560, 780] },
  strip: { x: 860, from: 120, to: 600 },             // the kitchen counter's under-cabinet light
  bars: { x: 200, z: 800, step: 33 },                 // the energy bars, from the panel in the hallway corner
  curtain: { y: 55, from: 255, to: 390 },             // the living-room window on the top wall (owner 2026-11-03)
  rings: [1240, 840],                                 // the water sensor on the bathroom floor
};

const root = document.querySelector('.dagur'), svg = root && root.querySelector('.dsvg');
if (root && svg && !matchMedia('(prefers-reduced-motion: reduce)').matches) init();

function init() {
  const S = HOUSE.widthM / HOUSE.w, H = 1.0, DOOR = 1.0, SILL = 0.55, FW = HOUSE.widthM, FD = HOUSE.h * S;
  const P = (px, py) => [px * S, py * S];
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const box = document.createElement('div'); box.className = 'd3';
  const labels = document.createElement('div'); labels.className = 'd3labels'; box.appendChild(labels);
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false }); } catch (e) { return; }
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  box.insertBefore(renderer.domElement, labels);
  svg.parentNode.insertBefore(box, svg);
  svg.classList.add('d3off');

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 600 / 440, 0.1, 60);
  const accent = new THREE.Color(css('--accent') || '#f5a524');

  // ---- the floor: the render, or the drawing when it fails to load ----
  const floorMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0 });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(FW, FD), floorMat);
  floor.rotation.x = -Math.PI / 2; floor.position.set(FW / 2, 0, FD / 2); scene.add(floor);
  const setMap = (tex) => { tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = renderer.capabilities.getMaxAnisotropy(); floorMat.map = tex; floorMat.needsUpdate = true; };
  new THREE.TextureLoader().load(HOUSE.img, setMap, undefined, paintDrawing);
  function paintDrawing() {
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
    const bg = css('--card') || '#fff', img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = 1200; c.height = 880;
      const g = c.getContext('2d'); g.fillStyle = bg; g.fillRect(0, 0, 1200, 880); g.drawImage(img, 0, 0, 1200, 880);
      setMap(new THREE.CanvasTexture(c));
    };
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(clone));
  }

  // ---- walls: segments split at the openings ----
  const wallMat = new THREE.MeshStandardMaterial({ color: 0xe4e6e9, transparent: true, opacity: 0.18, roughness: 0.9, depthWrite: false });
  const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.22 });
  function slab(x1, z1, x2, z2, t, y0, y1) {
    const len = Math.hypot(x2 - x1, z2 - z1), g = new THREE.BoxGeometry(len, y1 - y0, t);
    const m = new THREE.Mesh(g, wallMat); m.position.set((x1 + x2) / 2, (y0 + y1) / 2, (z1 + z2) / 2); m.rotation.y = -Math.atan2(z2 - z1, x2 - x1);
    m.add(new THREE.LineSegments(new THREE.EdgesGeometry(g), edgeMat)); scene.add(m); return m;
  }
  function wall(ax, az, bx, bz, t, ops) {
    const horiz = az === bz, a = horiz ? ax : az, b = horiz ? bx : bz, fixed = horiz ? az : ax;
    const pt = (v) => horiz ? P(v, fixed) : P(fixed, v);
    let cur = Math.min(a, b); const end = Math.max(a, b);
    for (const [o1, o2, kind] of [...ops].sort((p, q) => p[0] - q[0])) {
      if (o1 > cur) slab(...pt(cur), ...pt(o1), t, 0, H);
      if (kind === 'win') slab(...pt(o1), ...pt(o2), t, 0, SILL);
      if (DOOR < H) slab(...pt(o1), ...pt(o2), t, DOOR, H);
      cur = o2;
    }
    if (cur < end) slab(...pt(cur), ...pt(end), t, 0, H);
  }
  HOUSE.walls.forEach((w) => wall(...w));
  // the front door leaf on its hinge
  const [hx, hz] = P(...HOUSE.frontDoor.hinge);
  const door = new THREE.Group(); door.position.set(hx, 0, hz); scene.add(door);
  const dw = HOUSE.frontDoor.width * S;
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(dw, DOOR, 0.05), new THREE.MeshStandardMaterial({ color: 0xd9c4a0, roughness: 0.8, transparent: true, opacity: 0.85 }));
  leaf.position.set(dw / 2, DOOR / 2, 0); door.add(leaf);

  // ---- light ----
  scene.add(new THREE.AmbientLight(0xffffff, 0.45));
  const sun = new THREE.DirectionalLight(0xffffff, 0.6); sun.position.set(-4, 6, 2); scene.add(sun);
  const glowTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
    const r = g.createRadialGradient(64, 64, 0, 64, 64, 64); r.addColorStop(0, 'rgba(255,220,150,1)'); r.addColorStop(0.3, 'rgba(255,200,110,.6)'); r.addColorStop(1, 'rgba(255,180,80,0)');
    g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c);
  })();
  const lamps = {}, LP = {};
  for (const k in HOUSE.lights) {
    const [x, z] = P(...HOUSE.lights[k]); LP[k] = [x, z];
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    sp.position.set(x, H + 0.05, z); scene.add(sp);
    const pl = new THREE.PointLight(0xffd28a, 0, 5, 1.4); pl.position.set(x, H - 0.1, z); scene.add(pl);
    lamps[k] = { sp, pl, level: 0, target: 0 };
  }
  const st = HOUSE.strip, [sx, sz1] = P(st.x, st.from), sz2 = st.to * S;
  const stripMat = new THREE.MeshBasicMaterial({ color: 0xffd28a, transparent: true, opacity: 0 });
  const strip = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.03, sz2 - sz1), stripMat); strip.position.set(sx, 0.75, (sz1 + sz2) / 2); scene.add(strip);
  const stripL = new THREE.PointLight(0xffd28a, 0, 2.5, 1.8); stripL.position.set(sx - 0.1, 0.65, (sz1 + sz2) / 2); scene.add(stripL);
  lamps.strip = { sp: strip, pl: stripL, level: 0, target: 0, bar: true };

  // ---- scene props ----
  const bars = [], BARS = [3, 5, 4, 22, 12, 6, 5, 4, 4, 5, 9, 26, 34, 18, 8];
  const barMat = new THREE.MeshStandardMaterial({ color: accent, emissive: accent, emissiveIntensity: 0.35, roughness: 0.6 });
  BARS.forEach((h, i) => {
    const [bx, bz] = P(HOUSE.bars.x + i * HOUSE.bars.step, HOUSE.bars.z);
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.6, 0.07), barMat); m.position.set(bx, 0, bz); m.scale.y = 0.001; scene.add(m); bars.push([m, h / 34]);
  });
  const cu = HOUSE.curtain, cw = (cu.to - cu.from) * S;
  // a pleated band along the window, inside the room, seen from above like the curtains of a dollhouse render
  const curtain = new THREE.Mesh(new THREE.BoxGeometry(cw, H - SILL, 0.12), new THREE.MeshStandardMaterial({ color: 0xe6ded0, roughness: 1 }));
  curtain.geometry.translate(cw / 2, 0, 0);
  curtain.position.set(cu.from * S, (H + SILL) / 2, cu.y * S + 0.42); curtain.scale.x = 0.001; scene.add(curtain);
  const [rx, rz] = P(...HOUSE.rings);
  const rings = [0, 1].map(() => { const r = new THREE.Mesh(new THREE.RingGeometry(0.16, 0.2, 48), new THREE.MeshBasicMaterial({ color: 0x4aa3ff, transparent: true, opacity: 0, side: THREE.DoubleSide })); r.rotation.x = -Math.PI / 2; r.position.set(rx, 0.02, rz); scene.add(r); return r; });

  // ---- scenes: light levels, camera, sky, labels, animation per scene ----
  const CAM = {
    // steep views, as the dollhouse renders are seen: the floor image carries its own perspective, a low camera fights it
    1: [[6.4, 6.4, 4.2], [4.7, 0, 1.5]], 2: [[3.4, 6.6, 4.3], [3.0, 0, 1.5]], 3: [[1.8, 6.4, 6.4], [2.4, 0, 3.3]],
    4: [[-0.2, 6.2, 6.2], [1.3, 0, 3.2]], 5: [[2.4, 6.2, 3.6], [1.7, 0, 0.9]], 6: [[6.8, 6.4, 6.0], [5.0, 0, 3.2]], 7: [[3.0, 10.5, 5.6], [3.0, 0, 2.1]],
  };
  const LEVEL = { 1: { bad: .15, strip: .15 }, 2: { eldhus: .6, strip: 1, stofa: .5, bad: .5, forstofa: .5 }, 3: { eldhus: .6, strip: 1, stofa: .5, bad: .5, forstofa: .5, herbergi: .5 },
    4: {}, 5: { stofa: .7, eldhus: .35, forstofa: .3, herbergi: .4 }, 6: { forstofa: .12 }, 7: { stofa: .4, eldhus: .4, herbergi: .4, bad: .4, forstofa: .4 } };
  const SKY = { 1: '#0b1020', 2: '#2b3554', 3: '#a9c3da', 4: '#c3d6e6', 5: '#5a3b45', 6: '#090e1c', 7: '#171c28' };
  const SUN = { 1: [0.05, '#8fa0ff'], 2: [0.3, '#ffd9b0'], 3: [0.9, '#ffffff'], 4: [1.0, '#ffffff'], 5: [0.5, '#ff9a4a'], 6: [0.05, '#8fa0ff'], 7: [0.4, '#ffffff'] };
  const OFF = ['herbergi', 'bad', 'eldhus', 'strip', 'stofa', 'forstofa'];
  const at = (k, y, dx = 0, dz = 0) => [LP[k][0] + dx, y, LP[k][1] + dz];
  const LABELS = {
    1: [[at('herbergi', 1.3, 0, -0.4), '04:50', 'bub', 0.2], [at('bad', 1.5), '10 %', 'tag', 0.8], [[sx - 0.1, 1.2, (sz1 + sz2) / 2], '10 %', 'tag', 1.0]],
    2: [[at('eldhus', 1.5), '60 %', 'tag', 1.2], [at('eldhus', 1.0, 0.3, 1.0), 'haldið inni = dimmað', 'bub', 0.4]],
    3: [[[2.6, 1.4, 3.95], 'Allt af', 'bub', 0.3], [at('stofa', 1.1, 0.6, -0.4), 'straujárn af', 'tag', 1.6]],
    4: [[[P(HOUSE.bars.x + 7 * HOUSE.bars.step, 0)[0], 0.9, HOUSE.bars.z * S], 'kWh í dag', 'tag', 0.5]],
    5: [[[(cu.from + cu.to) / 2 * S, 1.3, cu.y * S + 0.42], 'gluggatjöld', 'tag', 1.2], [at('stofa', 1.5), 'kvöldstilling', 'tag', 0.6], [at('bad', 1.0, -0.4, -0.3), '21 °C', 'bub', 0.9]],
    6: [[at('forstofa', 1.5), '10 %', 'tag', 0.4], [[rx, 0.9, rz], 'Vatn í baðherbergi', 'note', 1.2]],
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
    const cw2 = box.clientWidth, ch = Math.round(cw2 * 440 / 600);
    if (cw2 !== w || ch !== h) { w = cw2; h = ch; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
    const t = (now - t0) / 1000, k = ease(t / 1.8);
    const drift = Math.sin(now / 4000) * 0.06;
    camera.position.lerpVectors(camFrom, camTo, k); camera.position.x += drift;
    look.lerpVectors(lookFrom, lookTo, k); camera.lookAt(look);
    scene.background.lerpColors(skyFrom, skyTo, k); scene.fog.color.copy(scene.background);
    sun.color.lerp(sunTo, 0.05); sun.intensity += (sunI - sun.intensity) * 0.05;
    if (cur === 5) sun.position.set(-4, 6 - 4 * ease(t / 3), 2); else sun.position.set(-4, 6, 2);
    for (const k in lamps) {
      const L = lamps[k]; let target = L.target;
      if (cur === 3) target = t > 0.6 + OFF.indexOf(k) * 0.45 ? 0 : target;
      if (cur === 6 && k === 'forstofa') target = t > 3.2 ? 0 : target;
      L.level += (target - L.level) * 0.08;
      if (L.bar) { L.sp.material.opacity = Math.min(1, L.level * 1.5); L.pl.intensity = L.level * 6; }
      else { L.sp.material.opacity = Math.min(1, L.level * 1.6); L.sp.scale.setScalar(0.6 + L.level * 1.6); L.pl.intensity = L.level * 14; }
    }
    const dt = cur === 3 ? -1.1 * ease((t - 0.2) / 1.2) : 0; door.rotation.y += (dt - door.rotation.y) * 0.1;
    bars.forEach(([m, f], i) => { const s = cur === 4 ? f * ease((t - 0.4 - i * 0.07) / 0.6) : 0; m.scale.y = Math.max(0.001, s); m.position.y = m.scale.y / 2; });
    curtain.scale.x += ((cur === 5 ? ease((t - 0.8) / 1.4) : 0) - curtain.scale.x) * 0.1; if (curtain.scale.x < 0.001) curtain.scale.x = 0.001;
    rings.forEach((r, i) => { const p = cur === 6 ? ((t * 0.7 + i * 0.5) % 1) : 0; r.scale.setScalar(0.4 + p * 2.4); r.material.opacity = cur === 6 ? (1 - p) * 0.8 : 0; });
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
