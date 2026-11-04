/* Einn dagur in 3D (owner 2026-11-03, "meira 3D", "svona 3D" with a furnished render as the reference, then "Vá!"):
   the scene player's house as a small film, built with Three.js over a rendered floor. The floor is
   img/dagur-floor.jpg, a top-down furnished render of the sample house (generated in Canva on 2026-11-03,
   1456 x 1088 px), cut to the house's outline so it floats; the walls rise from it as half-transparent slabs.
   The film look is this file's own post-processing (no addons, one CDN import): HDR render, bloom in three levels,
   a horizontal lens streak, tilt-shift (a miniature's focus band), radial blur while the camera flies, grade,
   vignette, grain. Around the house: stars, northern lights and snow at night, drifting cloud shadow by day. In the
   house: ignition rings per lamp, sun patches and shafts through the windows, dust, and signals
   that fly as arcs from the thing that decides to the thing that obeys. A clock runs the day forward between scenes.
   site.js still runs the scenes: this file watches data-scene on .dagur. Quality steps down by itself when the
   frames get slow (data-q on .d3 shows the step; step 3 is no post-processing). If the floor image fails, the SVG
   drawing is painted on the floor instead; without WebGL, with prefers-reduced-motion, or if Three.js does not
   load, the SVG player stays as it is. Image px -> metres: the image is 6.0 m wide. */
import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.min.js';

// ---- the house, in pixels of the floor image ----
const HOUSE = {
  img: 'img/dagur-floor.jpg', w: 1456, h: 1088, widthM: 6.0,
  outline: [[82, 56], [1374, 56], [1422, 935], [1422, 1016], [22, 1016], [20, 935]], // the building in the render, without its white paper
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
  panel: [115, 880],                                  // the board in the hallway corner
  curtain: { y: 55, from: 255, to: 390 },             // the living-room window on the top wall (owner 2026-11-03)
  rings: [1240, 840],                                 // the water sensor on the bathroom floor
  clock: [1282, 570],                                 // the alarm clock on the bedside table (owner 2026-11-03)
  sunTop: [[255, 390], [615, 735]],                   // windows the sun comes through: top wall, x from-to in px
  sunTopFloor: 180,                                   // where the floor starts below the top wall in the render
  sunRight: { x: 1340, from: 230, to: 430 },          // and the bedroom window on the right wall
};

const root = document.querySelector('.dagur'), svg = root && root.querySelector('.dsvg');
if (root && svg && !matchMedia('(prefers-reduced-motion: reduce)').matches) init();

function init() {
  const S = HOUSE.widthM / HOUSE.w, H = 1.0, DOOR = 1.0, SILL = 0.55, FW = HOUSE.widthM, FD = HOUSE.h * S;
  const P = (px, py) => [px * S, py * S];
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const box = document.createElement('div'); box.className = 'd3';
  const labels = document.createElement('div'); labels.className = 'd3labels'; box.appendChild(labels);
  const timeEl = document.createElement('div'); timeEl.className = 'd3time'; box.appendChild(timeEl);
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false, powerPreference: 'high-performance' }); } catch (e) { return; }
  box.insertBefore(renderer.domElement, labels);
  svg.parentNode.insertBefore(box, svg);
  svg.classList.add('d3off');

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 600 / 440, 0.1, 80);
  const accent = new THREE.Color(css('--accent') || '#f5a524');
  const hdr = (c, f) => new THREE.Color(c).multiplyScalar(f);
  const WARM = 0xffd28a, AMBER = 0xf5a524, BLUE = 0x4aa3ff;

  // ---- the world round the house: sky colour, stars and northern lights by night, cloud shadow by day ----
  const world = new THREE.ShaderMaterial({
    uniforms: { uT: { value: 0 }, uNight: { value: 1 }, uAur: { value: 0 }, uSky: { value: new THREE.Color('#0b1020') } },
    toneMapped: false,
    vertexShader: 'varying vec2 vP; void main(){ vec4 w = modelMatrix * vec4(position, 1.); vP = w.xz; gl_Position = projectionMatrix * viewMatrix * w; }',
    fragmentShader: `
      varying vec2 vP; uniform float uT, uNight, uAur; uniform vec3 uSky;
      float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.-2.*f);
        return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y); }
      void main(){
        vec2 q = vP - vec2(3., 2.25);
        vec3 c = uSky * (1.15 - 0.045 * length(q));
        if (uNight < .99) c *= 1. + (1. - uNight) * (0.34 * noise(q * .22 + uT * .03) - .17);           // cloud shadow
        vec2 g = q * 2.6, id = floor(g), f = fract(g) - .5; float h = hash(id);        // stars
        if (uNight > .01 && h > .93) { float tw = .55 + .45 * sin(uT * (1. + 3. * h) + h * 90.);
          c += vec3(.8, .9, 1.2) * uNight * tw * smoothstep(.09, .0, length(f - (hash(id + 3.) - .5) * .6)) * (h - .9) * 16.; }
        if (uAur > .004) for (int i = 0; i < 3; i++) {                                 // northern lights: three drifting curtains
          float n = float(i);
          float line = q.y + (n - 1.) * 4.3 + 1.1 * sin(q.x * .42 + uT * .13 + n * 2.1) + 1.5 * (noise(vec2(q.x * .3 + uT * .05, n * 7.)) - .5);
          float rays = .45 + .55 * noise(vec2(q.x * 3.2 + uT * .35, n * 3.));
          float a = exp(-line * line * 1.5) * rays * rays;
          vec3 col = mix(vec3(.15, 1.25, .62), vec3(.5, .35, 1.25), smoothstep(0., 1.4, line + n * .5));
          c += col * a * uAur * .62;
        }
        gl_FragColor = vec4(c, 1.);
        #include <colorspace_fragment>
      }`,
  });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(120, 120), world); ground.rotation.x = -Math.PI / 2; ground.position.set(3, -0.04, 2.2); scene.add(ground);
  scene.background = new THREE.Color('#0b1020');

  // ---- the floor: the render cut to the building's outline, or the drawing when it fails to load ----
  const floorMat = new THREE.MeshLambertMaterial({ color: 0xffffff, side: THREE.DoubleSide });
  const fg = new THREE.BufferGeometry(), ol = HOUSE.outline, fp = [], fuv = [], fn = [], fi = [];
  ol.forEach(([x, y]) => { fp.push(x * S, 0, y * S); fuv.push(x / HOUSE.w, 1 - y / HOUSE.h); fn.push(0, 1, 0); });
  for (let i = 1; i < ol.length - 1; i++) fi.push(0, i, i + 1);
  fg.setAttribute('position', new THREE.Float32BufferAttribute(fp, 3)); fg.setAttribute('uv', new THREE.Float32BufferAttribute(fuv, 2)); fg.setAttribute('normal', new THREE.Float32BufferAttribute(fn, 3)); fg.setIndex(fi);
  scene.add(new THREE.Mesh(fg, floorMat));
  const setMap = (tex) => { tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = renderer.capabilities.getMaxAnisotropy(); floorMat.map = tex; floorMat.needsUpdate = true; renderer.initTexture(tex); };
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

  // ---- walls: segments split at the openings, in one group so they can rise ----
  const walls = new THREE.Group(); scene.add(walls);
  const wallMat = new THREE.MeshLambertMaterial({ color: 0xe4e6e9, transparent: true, opacity: 0.06, depthWrite: false });
  const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.22 });
  function slab(x1, z1, x2, z2, t, y0, y1) {
    const len = Math.hypot(x2 - x1, z2 - z1), g = new THREE.BoxGeometry(len, y1 - y0, t);
    const m = new THREE.Mesh(g, wallMat); m.position.set((x1 + x2) / 2, (y0 + y1) / 2, (z1 + z2) / 2); m.rotation.y = -Math.atan2(z2 - z1, x2 - x1);
    m.add(new THREE.LineSegments(new THREE.EdgesGeometry(g), edgeMat)); walls.add(m); return m;
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
  const door = new THREE.Group(); door.position.set(hx, 0, hz); walls.add(door);
  const dw = HOUSE.frontDoor.width * S;
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(dw, DOOR, 0.05), new THREE.MeshStandardMaterial({ color: 0xd9c4a0, roughness: 0.8, transparent: true, opacity: 0.85 }));
  leaf.position.set(dw / 2, DOOR / 2, 0); door.add(leaf);

  // ---- light ----
  const amb = new THREE.AmbientLight(0xffffff, 0.3); scene.add(amb);
  const sun = new THREE.DirectionalLight(0xffffff, 0.2); sun.position.set(-4, 6, 2); scene.add(sun);
  const glowTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
    const r = g.createRadialGradient(64, 64, 0, 64, 64, 64); r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.25, 'rgba(255,255,255,.5)'); r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c);
  })();
  const glowSprite = (color) => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0 })); return s; };
  const additive = (color) => new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, toneMapped: false });
  const lamps = {}, LP = {};
  for (const k in HOUSE.lights) {
    const [x, z] = P(...HOUSE.lights[k]); LP[k] = [x, z];
    const sp = glowSprite(hdr(WARM, 1.5)); sp.position.set(x, H + 0.05, z); scene.add(sp);
    const pl = new THREE.PointLight(0xffd28a, 0, 5.5, 1.4); pl.position.set(x, H - 0.1, z); scene.add(pl);
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.9, 1, 64), additive(hdr(WARM, 2.4))); ring.rotation.x = -Math.PI / 2; ring.position.set(x, 0.03, z); scene.add(ring);
    lamps[k] = { sp, pl, ring, level: 0, target: 0, was: 0, fire: -1e9 };
  }
  const st = HOUSE.strip, [sx, sz1] = P(st.x, st.from), sz2 = st.to * S;
  const stripMat = new THREE.MeshBasicMaterial({ color: hdr(WARM, 4), transparent: true, opacity: 0, toneMapped: false });
  const strip = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.03, sz2 - sz1), stripMat); strip.position.set(sx, 0.75, (sz1 + sz2) / 2); scene.add(strip);
  const stripL = new THREE.PointLight(0xffd28a, 0, 2.5, 1.8); stripL.position.set(sx - 0.1, 0.65, (sz1 + sz2) / 2); scene.add(stripL);
  lamps.strip = { sp: strip, pl: stripL, level: 0, target: 0, was: 0, fire: -1e9, bar: true };
  LP.strip = [sx, (sz1 + sz2) / 2];

  // ---- sun through the windows: a patch on the floor and a shaft in the air, moved per scene ----
  const fadeTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'), im = g.createImageData(64, 64);
    for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) {
      const u = (x + .5) / 64, w = Math.min(1, Math.min(u, 1 - u) * 5), f = Math.pow(1 - (y + .5) / 64, 1.3), e = Math.min(1, (y + .5) / 64 * 8);
      const l = 255 * w * w * (3 - 2 * w) * f * e, i = (y * 64 + x) * 4; im.data[i] = im.data[i + 1] = im.data[i + 2] = l; im.data[i + 3] = 255;
    }
    g.putImageData(im, 0, 0); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  })();
  const quad = () => {
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(12), 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute([0, 1, 1, 1, 1, 0, 0, 0], 2)); g.setIndex([0, 1, 2, 0, 2, 3]);
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: fadeTex, color: 0xffffff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, toneMapped: false }));
    m.frustumCulled = false; scene.add(m); return m;
  };
  const setQuad = (m, a) => { const p = m.geometry.attributes.position; a.forEach((v, i) => p.setXYZ(i, v[0], v[1], v[2])); p.needsUpdate = true; };
  const beams = [...HOUSE.sunTop.map(([a, b], i) => ({ top: true, a: a * S, b: b * S, patch: quad(), shaft: quad(), living: i === 0 })),
    { top: false, a: HOUSE.sunRight.from * S, b: HOUSE.sunRight.to * S, patch: quad(), shaft: quad() }];
  const SUNP = { // len m, skew m/m, strength top windows, strength right window, colour
    1: [1, 0, 0, 0, '#000000'], 2: [1.3, 0.4, 0.3, 0.2, '#ffb070'], 3: [1.6, 0.2, 0.4, 0.15, '#fff0d4'], 4: [1.1, -0.05, 0.5, 0, '#fff6e6'],
    5: [1.7, -0.3, 0.6, 0, '#ff7a30'], 6: [1, 0, 0, 0, '#000000'], 7: [1, 0, 0, 0, '#000000'] };
  const sunNow = { len: 1, skew: 0, top: 0, right: 0, col: new THREE.Color(0) }, sunCol = new THREE.Color();

  // ---- particles: snow outside by night, dust in the sun ----
  function particles(n, gen, color, size, speed, range, sway) {
    const pos = new Float32Array(n * 3), seed = new Float32Array(n);
    for (let i = 0; i < n; i++) { const p = gen(); pos.set(p, i * 3); seed[i] = Math.random(); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aS', new THREE.BufferAttribute(seed, 1));
    const m = new THREE.ShaderMaterial({
      uniforms: { uT: { value: 0 }, uA: { value: 0 }, uPx: { value: 1 }, uC: { value: new THREE.Color(color) }, uSize: { value: size }, uSpeed: { value: speed }, uR: { value: range }, uSway: { value: sway } },
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: `attribute float aS; uniform float uT, uPx, uSize, uSpeed, uR, uSway; varying float vS;
        void main(){ vec3 p = position; vS = aS; p.y = mod(p.y + uT * uSpeed * (.6 + aS), uR);
          if (uSpeed < 0.) p.y = uR - mod(position.y - uT * uSpeed * (.6 + aS), uR);
          p.x += sin(uT * .6 + aS * 40.) * uSway; p.z += cos(uT * .47 + aS * 70.) * uSway;
          vec4 m = modelViewMatrix * vec4(p, 1.); gl_PointSize = uSize * uPx * (.5 + aS) / -m.z; gl_Position = projectionMatrix * m; }`,
      fragmentShader: `uniform vec3 uC; uniform float uA, uT; varying float vS;
        void main(){ float d = length(gl_PointCoord - .5); float a = smoothstep(.5, .05, d) * uA * (.5 + .5 * sin(uT * 1.3 + vS * 50.));
          gl_FragColor = vec4(uC * a, 1.); }`,
    });
    const pts = new THREE.Points(g, m); pts.frustumCulled = false; scene.add(pts); return { pts, m, n };
  }
  const snow = particles(420, () => {
    let x, z; do { x = -5 + Math.random() * 16; z = -5 + Math.random() * 15; } while (x > -0.1 && x < 6.1 && z > -0.1 && z < 4.5);
    return [x, Math.random() * 5, z];
  }, 0xffffff, 20, -0.5, 5, 0.22);
  const dust = particles(160, () => [0.4 + Math.random() * 5.2, Math.random() * 1.1, 0.3 + Math.random() * 3.7], 0xffe6b8, 11, 0.03, 1.1, 0.1);

  // ---- scene props ----
  const bars = [], BARS = [3, 5, 4, 22, 12, 6, 5, 4, 4, 5, 9, 26, 34, 18, 8];
  const barMat = new THREE.MeshLambertMaterial({ color: accent, emissive: accent, emissiveIntensity: 0.9 });
  BARS.forEach((h, i) => {
    const [bx, bz] = P(HOUSE.bars.x + i * HOUSE.bars.step, HOUSE.bars.z);
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.6, 0.07), barMat); m.position.set(bx, 0, bz); m.scale.y = 0.001; scene.add(m); bars.push([m, h / 34]);
  });
  const cu = HOUSE.curtain, cw = (cu.to - cu.from) * S;
  // a pleated curtain along the window, inside the room, from the wall top to the floor; it comes down from the top (owner 2026-11-03)
  const curtainGeo = new THREE.BoxGeometry(cw, H, 0.1, 42, 1, 1);
  { const p = curtainGeo.attributes.position; for (let i = 0; i < p.count; i++) p.setZ(i, p.getZ(i) + Math.sin(p.getX(i) * 62) * 0.035); p.needsUpdate = true; curtainGeo.computeVertexNormals(); }
  curtainGeo.translate(cw / 2, -H / 2, 0);
  const curtain = new THREE.Mesh(curtainGeo, new THREE.MeshLambertMaterial({ color: 0xbfb6a6 }));
  curtain.position.set(cu.from * S, H, cu.y * S + 0.42); curtain.scale.y = 0.001; curtain.visible = false; scene.add(curtain);
  const ripples = (x, y, z, color, n) => Array.from({ length: n }, () => {
    const r = new THREE.Mesh(new THREE.RingGeometry(0.16, 0.2, 48), additive(color));
    r.rotation.x = -Math.PI / 2; r.position.set(x, y, z); scene.add(r); return r;
  });
  const [rx, rz] = P(...HOUSE.rings);
  const rings = ripples(rx, 0.03, rz, hdr(BLUE, 3), 3);
  // the alarm clock on the bedside table, lying at the render's own floor level so it stays on the table from every view
  const [kx, kz] = P(...HOUSE.clock);
  const clock = new THREE.Group(); clock.position.set(kx, 0.02, kz); clock.rotation.x = -0.75; scene.add(clock);
  const clockBody = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.13, 0.07), new THREE.MeshStandardMaterial({ color: 0x3a4152, roughness: 0.5, emissive: 0x151922 }));
  clockBody.position.y = 0.07; clock.add(clockBody);
  const faceCan = document.createElement('canvas'); faceCan.width = 128; faceCan.height = 80;
  { const g = faceCan.getContext('2d'); g.fillStyle = '#06080e'; g.fillRect(0, 0, 128, 80); g.fillStyle = '#ffb24a'; g.font = '700 42px Inter, system-ui, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('04:50', 64, 42); }
  const clockFace = new THREE.Mesh(new THREE.PlaneGeometry(0.155, 0.1), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(faceCan), color: 0x333333, toneMapped: false }));
  clockFace.material.map.colorSpace = THREE.SRGBColorSpace;
  clockFace.position.set(0, 0.07, 0.037); clock.add(clockFace);
  const bellMat = new THREE.MeshStandardMaterial({ color: 0xd8dde6, roughness: 0.3, metalness: 0.5, emissive: 0x333333 });
  [-0.055, 0.055].forEach((dx) => { const b = new THREE.Mesh(new THREE.SphereGeometry(0.036, 16, 12), bellMat); b.position.set(dx, 0.16, 0); clock.add(b); });
  const clockSp = glowSprite(hdr(0xffb24a, 2.6)); clockSp.position.set(0, 0.1, 0.05); clockSp.scale.setScalar(0.55); clock.add(clockSp);
  const bellRings = ripples(kx, 0.05, kz, hdr(0xffb24a, 3), 3);

  // ---- signals: arcs that fly from the thing that decides to the thing that obeys ----
  const at = (k, y, dx = 0, dz = 0) => [LP[k][0] + dx, y, LP[k][1] + dz];
  const [panx, panz] = P(...HOUSE.panel);
  const PT = {
    clock: [kx, 0.15, kz], panel: [panx, 0.35, panz], sw: at('eldhus', 0.7, 0.3, 1.0), door: [hx + dw / 2, 0.8, hz], sensor: [rx, 0.05, rz],
    curtain: [(cu.from + cu.to) / 2 * S, 0.9, cu.y * S + 0.42], therm: at('bad', 0.8, -0.4, -0.3), strip: [sx, 0.75, (sz1 + sz2) / 2],
    stofa: at('stofa', H), eldhus: at('eldhus', H), herbergi: at('herbergi', H), bad: at('bad', H), forstofa: at('forstofa', H),
  };
  const R = (a, b, delay, dur, col = AMBER, loop = 0) => ({ a, b, delay, dur, col, loop });
  const ROUTES = {
    1: [R('clock', 'bad', 1.5, 0.6, 0xffb24a), R('clock', 'strip', 1.5, 0.6, 0xffb24a)],
    2: [R('sw', 'eldhus', 0.15, 0.5), R('sw', 'strip', 0.25, 0.5), R('sw', 'stofa', 0.35, 0.55), R('sw', 'bad', 0.45, 0.6), R('sw', 'forstofa', 0.45, 0.55)],
    3: ['herbergi', 'bad', 'eldhus', 'strip', 'stofa', 'forstofa'].map((k, i) => R('door', k, 0.3 + i * 0.45, 0.35, 0xff7a4a)),
    4: ['stofa', 'eldhus', 'herbergi', 'bad', 'forstofa', 'strip'].map((k, i) => R(k, 'panel', 0.3 + i * 0.28, 0.9, AMBER, 1.7)),
    5: [R('panel', 'stofa', 0.2, 0.6), R('panel', 'eldhus', 0.3, 0.65), R('panel', 'herbergi', 0.4, 0.75), R('panel', 'forstofa', 0.3, 0.4), R('panel', 'curtain', 0.6, 0.6), R('panel', 'therm', 0.8, 0.8)],
    6: [R('sensor', 'panel', 0.9, 0.9, BLUE)],
    7: ['stofa', 'eldhus', 'herbergi', 'bad', 'forstofa', 'strip', 'curtain', 'sensor', 'clock'].map((k, i) => R('panel', k, 0.5 + i * 0.22, 0.9, i % 2 ? AMBER : 0x6fd0ff, 2.6)),
  };
  // when the light obeys: the moment the signal lands
  const LIGHT_AT = { 2: { eldhus: 0.65, strip: 0.75, stofa: 0.9, bad: 1.05, forstofa: 1.0 }, 5: { stofa: 0.8, eldhus: 0.95, herbergi: 1.15, forstofa: 0.7 }, 7: { stofa: 1.2, eldhus: 1.35, herbergi: 1.6, bad: 1.8, forstofa: 1.5, strip: 1.9 } };
  const arcs = {};
  function arcFor(a, b, col) {
    const key = a + '|' + b + '|' + col;
    if (arcs[key]) return arcs[key];
    const A = new THREE.Vector3(...PT[a]), B = new THREE.Vector3(...PT[b]);
    const mid = A.clone().lerp(B, 0.5); mid.y = Math.max(A.y, B.y) + 0.35 + A.distanceTo(B) * 0.32;
    const curve = new THREE.QuadraticBezierCurve3(A, mid, B);
    const SEG = 48, RAD = 5, mat = new THREE.MeshBasicMaterial({ color: hdr(col, 3.4), transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
    const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, SEG, 0.011, RAD, false), mat); tube.visible = false; tube.frustumCulled = false; scene.add(tube);
    const head = glowSprite(hdr(col, 4)); head.scale.setScalar(0.3); head.material.opacity = 1; head.visible = false; scene.add(head);
    return (arcs[key] = { curve, tube, head, SEG, RAD });
  }
  for (const n in ROUTES) ROUTES[n].forEach((r) => { r.arc = arcFor(r.a, r.b, r.col); });

  // ---- scenes: camera shots, light levels, colour, labels ----
  // a = the shot the camera flies to, b = where it drifts after tp seconds, over dp seconds; all steep from above,
  // as the dollhouse renders are seen: the floor image carries its own perspective, a low camera fights it
  const CAMS = {
    1: { a: [[kx + 0.7, 4.6, kz + 2.6], [kx - 0.1, 0, kz - 0.1]], b: [[5.5, 7.1, 5.5], [4.6, 0, 2.2]], tp: 2.0, dp: 3.2 },
    2: { a: [[3.4, 5.8, 4.1], [2.9, 0, 1.5]], b: [[3.0, 7.2, 4.9], [2.7, 0, 1.9]], tp: 1.8, dp: 3.2 },
    3: { a: [[2.7, 5.4, 6.3], [2.5, 0, 3.4]], b: [[2.6, 8.2, 6.7], [2.9, 0, 2.6]], tp: 1.6, dp: 3.4 },
    4: { a: [[0.8, 4.8, 5.7], [1.2, 0, 3.2]], b: [[2.3, 5.2, 5.9], [2.4, 0, 3.2]], tp: 1.9, dp: 4 },
    5: { a: [[1.9, 4.8, 3.2], [1.45, 0, 1.0]], b: [[2.6, 6.8, 4.5], [2.3, 0, 1.4]], tp: 2.8, dp: 3 },
    6: { a: [[3.2, 6.2, 5.6], [2.9, 0, 3.4]], b: [[5.6, 5.2, 5.8], [5.0, 0, 3.3]], tp: 1.6, dp: 2.6 },
    7: { a: [[3, 9.6, 5.3], [3, 0, 2.2]], b: [[3, 12, 6.2], [3, 0, 2.2]], tp: 1.6, dp: 7 },
  };
  const LEVEL = { 1: { bad: .15, strip: .15 }, 2: { eldhus: .6, strip: 1, stofa: .5, bad: .5, forstofa: .5 }, 3: { eldhus: .6, strip: 1, stofa: .5, bad: .5, forstofa: .5, herbergi: .5 },
    4: {}, 5: { stofa: .7, eldhus: .35, forstofa: .3, herbergi: .4 }, 6: { forstofa: .12 }, 7: { stofa: .4, eldhus: .4, herbergi: .4, bad: .4, forstofa: .4, strip: .5 } };
  const SKY = { 1: '#070b18', 2: '#2b3554', 3: '#a9c3da', 4: '#c3d6e6', 5: '#4a2d38', 6: '#060a16', 7: '#0a0f1e' };
  const SUN = { 1: [0.1, '#8fa0ff'], 2: [0.8, '#ffd9b0'], 3: [1.7, '#ffffff'], 4: [1.9, '#ffffff'], 5: [0.9, '#ff9a4a'], 6: [0.1, '#8fa0ff'], 7: [0.5, '#a9b8ff'] };
  const AMB = { 1: .6, 2: 1.1, 3: 2.2, 4: 2.4, 5: 1.0, 6: .45, 7: .85 };
  const NIGHT = { 1: 1, 2: .35, 3: 0, 4: 0, 5: .25, 6: 1, 7: 1 }, AUR = { 1: .75, 2: .12, 3: 0, 4: 0, 5: 0, 6: 1, 7: 1 }, SNOW = { 1: .9, 2: .4, 3: 0, 4: 0, 5: .15, 6: 1, 7: .8 }, DUST = { 1: 0, 2: .6, 3: 1, 4: 1, 5: .9, 6: 0, 7: 0 };
  const TINT = { 1: [.86, .93, 1.2], 2: [1.08, .98, .92], 3: [1, 1, 1], 4: [1.02, 1, .98], 5: [1.18, .96, .84], 6: [.82, .92, 1.25], 7: [.94, .96, 1.1] };
  const TIME = { 1: 290, 2: 390, 3: 480, 4: 720, 5: 1120, 6: 1630, 7: null }; // minutes; 03:10 is the next night
  const OFF = ['herbergi', 'bad', 'eldhus', 'strip', 'stofa', 'forstofa'];
  const LABELS = {
    1: [[at('bad', 1.5), '10 %', 'tag', 2.2], [[sx - 0.1, 1.2, (sz1 + sz2) / 2], '10 %', 'tag', 2.3]],
    2: [[at('eldhus', 1.5), '60 %', 'tag', 1.2], [at('eldhus', 1.0, 0.3, 1.0), 'haldið inni = dimmað', 'bub', 0.4]],
    3: [[[2.6, 1.4, 3.95], 'Allt af', 'bub', 0.3], [at('stofa', 1.1, 0.6, -0.4), 'straujárn af', 'tag', 1.6]],
    4: [[[P(HOUSE.bars.x + 7 * HOUSE.bars.step, 0)[0], 0.9, HOUSE.bars.z * S], 'kWh í dag', 'tag', 0.5]],
    5: [[[(cu.from + cu.to) / 2 * S, 1.3, cu.y * S + 0.42], 'gluggatjöld', 'tag', 1.2], [at('stofa', 1.5), 'kvöldstilling', 'tag', 0.6], [at('bad', 1.0, -0.4, -0.3), '21 °C', 'bub', 1.4]],
    6: [[at('forstofa', 1.5), '10 %', 'tag', 0.4], [[rx, 0.9, rz], 'Vatn í baðherbergi', 'note', 1.6]],
    7: [],
  };
  let cur = 0, prev = 0, prevT0 = 0, t0 = performance.now(), intro = -1;
  const LEAD = 0.6, SMOOTH = 0.75, labs = [];   // the scene's events start LEAD s after the camera sets off
  let skyFrom = new THREE.Color(SKY[1]), skyTo = skyFrom.clone(), sunTo = new THREE.Color('#fff'), sunI = 0, sunPar = SUNP[1], timeFrom = TIME[1];
  const look = new THREE.Vector3(3, 0, 2.2), base = new THREE.Vector3(3, 15, 7), tintNow = new THREE.Vector3(...TINT[1]);
  const setScene = (n) => {
    if (n === cur) return;
    timeFrom = cur && TIME[cur] != null && TIME[n] != null ? shownTime : TIME[n];
    prev = cur; prevT0 = t0; cur = n; t0 = performance.now();
    skyFrom = scene.background.clone(); skyTo = new THREE.Color(SKY[n]); sunTo = new THREE.Color(SUN[n][1]); sunI = SUN[n][0]; sunPar = SUNP[n];
    for (const k in lamps) lamps[k].target = LEVEL[n][k] || 0;
    labs.forEach((l) => { l.dying = t0; l.el.style.opacity = '0'; });
    const addLab = (cls, delay, p, html) => {
      const el = document.createElement('div'); el.className = 'lab ' + cls; if (html) el.innerHTML = html; labels.appendChild(el);
      if (p) { el.style.left = el.style.top = '0'; el.style.willChange = 'transform'; }
      labs.push({ el, d: delay, p, dying: 0, on: false }); return el;
    };
    for (const [p, text, cls, delay] of LABELS[n]) addLab(cls, delay, p).textContent = text;
    if (n === 7) addLab('end', 1.8, null, '<b>Snjallheimilið</b>Allt á heimanetinu, engin áskrift.<span>Fáðu verðbil á 2 mínútum</span>');
  };
  let shownTime = TIME[1];
  setScene(Number(root.dataset.scene) || 1);
  new MutationObserver(() => setScene(Number(root.dataset.scene) || 1)).observe(root, { attributes: true, attributeFilter: ['data-scene'] });

  // ---- post-processing: HDR scene -> bloom levels, streak, soft copy -> one composite ----
  const canHDR = renderer.capabilities.isWebGL2 && (renderer.extensions.has('EXT_color_buffer_float') || renderer.extensions.has('EXT_color_buffer_half_float'));
  const fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), fsScene = new THREE.Scene(), fsQuad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2)); fsQuad.frustumCulled = false; fsScene.add(fsQuad);
  const VS = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }';
  const brightMat = new THREE.ShaderMaterial({ depthTest: false, depthWrite: false, uniforms: { t: { value: null }, thr: { value: 1 } }, vertexShader: VS,
    fragmentShader: 'varying vec2 vUv; uniform sampler2D t; uniform float thr; void main(){ vec3 c = max(texture2D(t, vUv).rgb, vec3(0.)); float l = max(c.r, max(c.g, c.b)); if (!(l < 1e4)) { c = vec3(0.); l = 0.; } gl_FragColor = vec4(min(c, vec3(10.)) * smoothstep(thr, thr + .7, l), 1.); }' });
  const blurMat = new THREE.ShaderMaterial({ depthTest: false, depthWrite: false, uniforms: { t: { value: null }, d: { value: new THREE.Vector2() } }, vertexShader: VS,
    fragmentShader: 'varying vec2 vUv; uniform sampler2D t; uniform vec2 d; void main(){ vec3 c = texture2D(t, vUv).rgb * .227; c += (texture2D(t, vUv + d * 1.385).rgb + texture2D(t, vUv - d * 1.385).rgb) * .316; c += (texture2D(t, vUv + d * 3.23).rgb + texture2D(t, vUv - d * 3.23).rgb) * .07; gl_FragColor = vec4(c, 1.); }' });
  const compMat = new THREE.ShaderMaterial({ depthTest: false, depthWrite: false, toneMapped: false,
    uniforms: { t: { value: null }, soft: { value: null }, b0: { value: null }, b1: { value: null }, b2: { value: null }, streak: { value: null }, uZoom: { value: 0 }, uTilt: { value: 1 }, uExpo: { value: 1 }, uTime: { value: 0 }, uTint: { value: new THREE.Vector3(1, 1, 1) }, uBloom: { value: 1 } },
    vertexShader: VS,
    fragmentShader: `
      varying vec2 vUv; uniform sampler2D t, soft, b0, b1, b2, streak; uniform float uZoom, uTilt, uExpo, uTime, uBloom; uniform vec3 uTint;
      vec3 aces(vec3 x){ return clamp((x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14), 0., 1.); }
      float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      void main(){
        vec3 c = texture2D(t, vUv).rgb;
        if (uZoom > .002) { vec2 dir = (vUv - .5) * uZoom; vec3 s = c; for (int i = 1; i < 6; i++) s += texture2D(t, vUv - dir * float(i) / 5.).rgb; c = s / 6.; }
        float m = smoothstep(.3, .62, abs(vUv.y - .5)) * uTilt * .85;
        c = mix(c, texture2D(soft, vUv).rgb, m);
        c += (texture2D(b0, vUv).rgb * .3 + texture2D(b1, vUv).rgb * .45 + texture2D(b2, vUv).rgb * .6) * uBloom;
        c += texture2D(streak, vUv).rgb * vec3(.55, .7, 1.2) * .5 * uBloom;
        c *= uTint * uExpo;
        c = aces(c);
        vec2 q = vUv - .5; c *= 1. - dot(q, q) * .85;
        c = pow(c, vec3(1. / 2.2));
        c += (hash(vUv * 917. + uTime) - .5) * .022;
        gl_FragColor = vec4(c, 1.);
      }` });
  const opts = () => ({ type: THREE.HalfFloatType, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
  let rt = null, softA, softB, blooms = [], streakA, streakB;
  let q = !canHDR ? 3 : innerWidth < 700 ? 1 : 0, w = 0, h = 0, pr = 1, compiled = false, dirty = true;
  const dpr = () => Math.min(devicePixelRatio || 1, q === 0 ? 2 : q === 1 ? 1.5 : 1);
  function disposeTargets() { if (!rt) return; [rt, softA, softB, streakA, streakB, ...blooms.flat()].forEach((x) => x.dispose()); rt = null; blooms = []; }
  function buildTargets() {
    disposeTargets(); if (q >= 3 || !w) return;
    const W = Math.floor(w * pr), HH = Math.floor(h * pr);
    rt = new THREE.WebGLRenderTarget(W, HH, { type: THREE.HalfFloatType, samples: q === 0 ? 4 : 0, depthBuffer: true, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
    const mk = (d) => new THREE.WebGLRenderTarget(Math.max(2, W >> d), Math.max(2, HH >> d), opts());
    softA = mk(2); softB = mk(2); streakA = mk(3); streakB = mk(3);
    blooms = [1, 2, 3].map((d) => d + 1).map((d) => [mk(d), mk(d)]);
  }
  function pass(mat, target) { fsQuad.material = mat; renderer.setRenderTarget(target); renderer.render(fsScene, fsCam); }
  function blur(src, a, b) {
    const iw = 1 / a.width, ih = 1 / a.height;
    blurMat.uniforms.t.value = src.texture; blurMat.uniforms.d.value.set(iw, 0); pass(blurMat, b);
    blurMat.uniforms.t.value = b.texture; blurMat.uniforms.d.value.set(0, ih); pass(blurMat, a);
  }
  function setQuality(n) {
    q = n; box.dataset.q = String(q);
    pr = dpr(); renderer.setPixelRatio(q >= 3 ? pr : 1); renderer.setSize(q >= 3 ? w : Math.floor(w * pr), q >= 3 ? h : Math.floor(h * pr), false);
    renderer.toneMapping = q >= 3 ? THREE.ACESFilmicToneMapping : THREE.NoToneMapping;
    snow.pts.geometry.setDrawRange(0, q >= 1 ? snow.n >> 1 : snow.n); dust.pts.geometry.setDrawRange(0, q >= 1 ? dust.n >> 1 : dust.n);
    snow.m.uniforms.uPx.value = dust.m.uniforms.uPx.value = h * pr / 440 * 1.5;
    buildTargets();
  }

  // ---- render loop ----
  const ease = (x) => x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x);
  const back = (x) => { if (x <= 0) return 0; if (x >= 1) return 1; const c = 1.70158, y = x - 1; return 1 + (c + 1) * y * y * y + c * y * y; };
  let visible = false, seen = false, last = performance.now(), slow = performance.now(), good = 0, orb = 0, orbT = 0, orbV = 0, px = 0, py = 0, tpx = 0, tpy = 0, alarmS = 0, faceB = 0.15, ringA = 0;
  // a spring that keeps its speed when the target jumps: the camera never starts or stops with a jerk
  let sdv = 0;
  const sd = (c, tg, vel, st, d) => { const om = 2 / st, x = om * d, e = 1 / (1 + x + 0.48 * x * x + 0.235 * x * x * x), ch = c - tg, tmp = (vel + om * ch) * d; sdv = (vel - om * tmp) * e; return tg + (ch + tmp) * e; };
  const sd3 = (c, tg, vel, st, d) => { c.x = sd(c.x, tg.x, vel.x, st, d); vel.x = sdv; c.y = sd(c.y, tg.y, vel.y, st, d); vel.y = sdv; c.z = sd(c.z, tg.z, vel.z, st, d); vel.z = sdv; };
  const velP = new THREE.Vector3(), velL = new THREE.Vector3();
  new ResizeObserver(() => { dirty = true; }).observe(box);
  new IntersectionObserver((es) => {
    visible = es[0].isIntersecting;
    if (visible && !seen) { seen = true; intro = performance.now(); t0 = intro; slow = intro; good = 0; }     // the film starts when it is first seen
  }, { threshold: 0.05 }).observe(box);
  box.addEventListener('pointermove', (e) => { const r = box.getBoundingClientRect(); tpx = (e.clientX - r.left) / r.width * 2 - 1; tpy = (e.clientY - r.top) / r.height * 2 - 1; });
  box.addEventListener('pointerleave', () => { tpx = tpy = 0; });
  const v = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0), pA = new THREE.Vector3(), lA = new THREE.Vector3(), pT = new THREE.Vector3(), lT = new THREE.Vector3(), pos = new THREE.Vector3();
  const pad = (n) => String(n).padStart(2, '0');
  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible || document.hidden) { last = now; return; }
    const dt = now - last; last = now;
    // quality: too few frames over 1.5 s steps it down (50, 40 and 24 a second); a long gap restarts the count
    if (dt > 1500) { good = 0; slow = now; } else { good++; if (now - slow > 1500) { if (good / ((now - slow) / 1000) < [50, 40, 24, 0][q] && q < 3) setQuality(q + 1); good = 0; slow = now; } }
    if (dirty) { dirty = false; const cw2 = box.clientWidth, ch = Math.round(cw2 * 440 / 600); if (cw2 && (cw2 !== w || ch !== h)) { w = cw2; h = ch; camera.aspect = w / h; camera.updateProjectionMatrix(); setQuality(q); } }
    if (!w) return;
    if (!compiled) {  // every shader now, while the picture is still black, or each first use stutters in the middle of the film
      compiled = true; const hid = []; scene.traverse((o) => { if (!o.visible) { hid.push(o); o.visible = true; } });
      renderer.setRenderTarget(rt); renderer.compile(scene, camera); renderer.setRenderTarget(null); hid.forEach((o) => { o.visible = false; });
      renderer.initTexture(glowTex); renderer.initTexture(fadeTex);
    }
    const ds = Math.min(dt / 1000, 0.1), tc = (now - t0) / 1000, t = tc - LEAD, sec = now / 1000, C = CAMS[cur];
    const blend = 1 - Math.pow(0.93, dt / 16.7), soft = 1 - Math.pow(0.968, dt / 16.7);

    // the camera follows a target on a spring: over to the shot with a lift, then along to the next, and never stands still
    pA.set(...C.a[0]); lA.set(...C.a[1]); pT.set(...C.b[0]); lT.set(...C.b[1]);
    const k2 = ease((tc - C.tp) / C.dp); pA.lerp(pT, k2); lA.lerp(lT, k2);
    pA.y += (1 - ease(tc / 1.5)) * 1.1;
    sd3(base, pA, velP, SMOOTH, ds); sd3(look, lA, velL, SMOOTH, ds);
    const inFlight = Math.min(1, velP.length() / 6);
    orbT = cur === 7 ? orbT + ds * 0.28 * ease((t - 1) / 3) : 0;
    orb = sd(orb, orbT, orbV, 1.1, ds); orbV = sdv;
    const yaw = Math.sin(now / 6500) * 0.12 + orb;
    v.subVectors(base, look).applyAxisAngle(UP, yaw);
    camera.position.addVectors(look, v);
    camera.position.y += Math.sin(now / 5200) * 0.07;
    px += (tpx - px) * blend * 0.7; py += (tpy - py) * blend * 0.7;
    camera.position.x += px * 0.28; camera.position.z += py * 0.2;
    camera.lookAt(look);

    // the day: sky, sun, ambient, northern lights, snow, dust
    scene.background.lerpColors(skyFrom, skyTo, ease(tc / 2.6));
    world.uniforms.uSky.value.copy(scene.background); world.uniforms.uT.value = sec;
    world.uniforms.uNight.value += (NIGHT[cur] - world.uniforms.uNight.value) * blend * 0.5;
    world.uniforms.uAur.value += (AUR[cur] * (1 + 0.15 * Math.sin(sec * 0.7)) - world.uniforms.uAur.value) * blend * 0.4;
    sun.color.lerp(sunTo, blend * 0.7); sun.intensity += (sunI - sun.intensity) * blend * 0.7;
    amb.intensity += (AMB[cur] - amb.intensity) * blend * 0.6;
    if (cur === 5) sun.position.y += (2 - sun.position.y) * blend * 0.3; else sun.position.y += (6 - sun.position.y) * blend * 0.3;
    snow.m.uniforms.uT.value = dust.m.uniforms.uT.value = sec;
    snow.m.uniforms.uA.value += (SNOW[cur] - snow.m.uniforms.uA.value) * blend * 0.4;
    dust.m.uniforms.uA.value += (DUST[cur] * 0.9 - dust.m.uniforms.uA.value) * blend * 0.4;
    tintNow.lerp(v.set(...TINT[cur]), blend * 0.5);

    // the clock in the corner runs the day forward during the flight
    if (TIME[cur] != null) {
      shownTime = timeFrom + (TIME[cur] - timeFrom) * ease(tc / 2.1);
      const m = Math.round(shownTime) % 1440; const s = pad(Math.floor(m / 60)) + ':' + pad(m % 60);
      if (timeEl.textContent !== s) timeEl.textContent = s;
      timeEl.style.opacity = '1';
    } else timeEl.style.opacity = '0';

    // the lamps
    let li = 0;
    for (const k in lamps) {
      const L = lamps[k]; let target = L.target;
      if (cur === 1) target = t > 2.05 ? target : 0;                                // the lights answer the alarm
      if (cur === 3) target = t > 0.65 + OFF.indexOf(k) * 0.45 ? 0 : target;
      if (cur === 6 && k === 'forstofa') target = t > 3.2 ? 0 : target;
      const la = LIGHT_AT[cur] && LIGHT_AT[cur][k]; if (la && t < la) target = L.was;
      if (target > 0.01 && L.was <= 0.01) L.fire = now;                             // ignition: a flash and a ring on the floor
      L.was = target;
      L.level += (target - L.level) * soft;
      const age = (now - L.fire) / 900;
      const flash = age < 1 ? Math.exp(-age * 5) * 1.6 : 0;
      const lv = L.level * (1 + 0.05 * Math.sin(now / 900 + li++ * 1.7)) + flash * 0.25;
      if (L.bar) { L.sp.material.opacity = Math.min(1, lv * 1.5); L.pl.intensity = lv * 3.5; }
      else {
        const noBloom = q >= 3 ? 1.6 : 1; L.sp.material.opacity = Math.min(1, lv * 1.1 * noBloom); L.sp.scale.setScalar((0.35 + lv * 0.8) * noBloom); L.pl.intensity = lv * 7 * noBloom;
        L.ring.visible = age < 1; if (age < 1) { L.ring.scale.setScalar(0.1 + ease(age) * 1.1); L.ring.material.opacity = (1 - age) * 0.8; }
      }
    }

    // the sun through the windows
    sunNow.len += (sunPar[0] - sunNow.len) * blend; sunNow.skew += (sunPar[1] - sunNow.skew) * blend;
    sunNow.top += (sunPar[2] - sunNow.top) * blend * 0.6; sunNow.right += (sunPar[3] - sunNow.right) * blend * 0.6; sunNow.col.lerp(sunCol.set(sunPar[4]), blend * 0.6);
    const zf = HOUSE.sunTopFloor * S, xr = HOUSE.sunRight.x * S, zw = HOUSE.curtain.y * S;
    for (const b of beams) {
      const L = sunNow.len, sk = sunNow.skew;
      let A = b.top ? sunNow.top : sunNow.right;
      if (b.living) A *= 1 - curtain.scale.y;
      b.patch.visible = b.shaft.visible = A > 0.004;
      if (!b.patch.visible) continue;
      if (b.top) {
        setQuad(b.patch, [[b.a, .015, zf], [b.b, .015, zf], [b.b + sk * L, .015, zf + L], [b.a + sk * L, .015, zf + L]]);
        setQuad(b.shaft, [[b.a, H, zw], [b.b, H, zw], [b.b + sk * L, 0, zf + L], [b.a + sk * L, 0, zf + L]]);
      } else {
        setQuad(b.patch, [[xr, .015, b.a], [xr, .015, b.b], [xr - L, .015, b.b + sk * L], [xr - L, .015, b.a + sk * L]]);
        setQuad(b.shaft, [[xr + .3, H, b.a], [xr + .3, H, b.b], [xr - L, 0, b.b + sk * L], [xr - L, 0, b.a + sk * L]]);
      }
      b.patch.material.color.copy(sunNow.col); b.shaft.material.color.copy(sunNow.col);
      b.patch.material.opacity = A; b.shaft.material.opacity = A * 0.18;
    }

    // walls: they rise when the film starts; the edges glow at night and flash blue on the water alarm
    const r0 = intro > 0 ? (now - intro) / 1500 : 0; walls.scale.y = Math.max(0.001, back(r0));
    alarmS += ((cur === 6 && t > 1.6 ? 1 : 0) - alarmS) * blend; const alarm = alarmS * (0.5 + 0.5 * Math.sin(sec * 6));
    edgeMat.opacity = 0.2 + NIGHTNESS() * 0.14 + (r0 < 1.3 ? (1.3 - Math.max(r0, 0)) * 0.25 : 0) + alarm * 0.5;
    edgeMat.color.setRGB(1 - alarm * 0.7, 1 - alarm * 0.3, 1 + alarm * 2).multiplyScalar(r0 < 1.3 ? 1.4 : 1 + alarm);

    // scene props
    const dt3 = cur === 3 ? -1.1 * ease((t - 0.2) / 1.2) : 0; door.rotation.y += (dt3 - door.rotation.y) * blend; leaf.visible = door.rotation.y < -0.01; leaf.material.opacity = Math.min(0.85, -door.rotation.y * 3); // shut, the render's own door shows
    bars.forEach(([m, f], i) => { const s = cur === 4 ? f * back((t - 0.4 - i * 0.07) / 0.7) : 0; m.scale.y = Math.max(0.001, s > 0 ? s * (1 + 0.03 * Math.sin(sec * 3 + i)) : m.scale.y + (0.001 - m.scale.y) * soft); m.visible = m.scale.y > 0.005; m.position.y = m.scale.y * 0.3; });
    curtain.scale.y += ((cur === 5 ? ease((t - 0.8) / 2) : 0) - curtain.scale.y) * blend; if (curtain.scale.y < 0.001) curtain.scale.y = 0.001; curtain.visible = curtain.scale.y > 0.01;
    ringA += ((cur === 6 && t > 0.5 ? 1 : 0) - ringA) * blend; rings.forEach((r, i) => { const p = (sec * 0.7 + i / 3) % 1; r.visible = ringA > 0.01; r.scale.setScalar(0.4 + p * 3.2); r.material.opacity = ringA * (1 - p) * 0.55; });

    // the alarm: from 0.3 s into scene 1 the clock shakes, its face lights, rings leave it; a second burst at 2.6 s
    const ring = cur === 1 && ((t > 0.3 && t < 1.9) || (t > 2.6 && t < 4.2));
    clock.rotation.z = ring ? Math.sin(now / 28) * 0.17 : 0;
    clock.position.y = 0.02 + (ring ? Math.abs(Math.sin(now / 56)) * 0.03 : 0);
    const faceOn = cur === 1 && t > 0.3;
    faceB += ((faceOn ? (ring ? 3 + Math.sin(now / 90) : 2) : 0.15) - faceB) * blend; clockFace.material.color.setScalar(faceB);
    clockSp.material.opacity += ((ring ? 0.85 : faceOn ? 0.25 : 0) - clockSp.material.opacity) * blend;
    bellRings.forEach((r, i) => { const p = ring ? ((t * 1.6 + i / 3) % 1) : 0; r.visible = ring; r.scale.setScalar(0.3 + p * 2.8); r.material.opacity = ring ? (1 - p) * 0.8 : 0; });

    // the signals
    for (const key in arcs) { arcs[key].tube.visible = false; arcs[key].head.visible = false; }
    const drawRoutes = (list, tt0, fade) => {
      for (const r of list) {
        let tt = tt0 - r.delay; if (r.loop && tt > 0) tt %= r.loop;
        const p = tt / r.dur;
        if (p <= 0 || p >= 1.35) continue;
        const A = r.arc, hd = Math.min(p, 1), tail = Math.max(0, p - 0.35), per = A.RAD * 6;
        A.tube.visible = true; A.tube.material.opacity = 0.95 * fade; A.tube.geometry.setDrawRange(Math.floor(tail * A.SEG) * per, Math.max(1, Math.ceil((hd - tail) * A.SEG)) * per);
        if (p < 1) { A.head.visible = true; A.head.material.opacity = fade; A.curve.getPoint(hd, A.head.position); }
      }
    };
    if (prev && tc < 0.9) drawRoutes(ROUTES[prev], (now - prevT0) / 1000 - LEAD, 1 - ease(tc / 0.9));
    drawRoutes(ROUTES[cur], t, 1);

    // the labels
    for (let i = labs.length - 1; i >= 0; i--) {
      const l = labs[i];
      if (l.dying) { if (now - l.dying > 700) { l.el.remove(); labs.splice(i, 1); continue; } }
      else if (!l.on && t > l.d) { l.on = true; l.el.style.opacity = '1'; }
      if (!l.p) continue;
      v.set(l.p[0], l.p[1] + Math.sin(now / 1400 + i) * 0.03, l.p[2]).project(camera);
      l.el.style.transform = 'translate3d(' + ((v.x + 1) / 2 * w).toFixed(1) + 'px,' + ((1 - v.y) / 2 * h).toFixed(1) + 'px,0) translate(-50%,-100%)';
    }

    // draw
    const fade = intro > 0 ? ease((now - intro) / 700) : 0;
    if (q >= 3) { renderer.toneMappingExposure = fade; renderer.setRenderTarget(null); renderer.render(scene, camera); return; }
    renderer.setRenderTarget(rt); renderer.render(scene, camera);
    brightMat.uniforms.t.value = rt.texture; brightMat.uniforms.thr.value = -1; pass(brightMat, softA); blur(softA, softA, softB);
    brightMat.uniforms.thr.value = 1.05; pass(brightMat, blooms[0][0]);
    blur(blooms[0][0], blooms[0][0], blooms[0][1]);
    for (let i = 1; i < 3; i++) blur(blooms[i - 1][0], blooms[i][0], blooms[i][1]);
    // the lens streak: the small bloom smeared sideways
    blurMat.uniforms.t.value = blooms[1][0].texture; blurMat.uniforms.d.value.set(5 / streakA.width, 0); pass(blurMat, streakB);
    blurMat.uniforms.t.value = streakB.texture; blurMat.uniforms.d.value.set(13 / streakA.width, 0); pass(blurMat, streakA);
    const U = compMat.uniforms;
    U.t.value = rt.texture; U.soft.value = softA.texture; U.b0.value = blooms[0][0].texture; U.b1.value = blooms[1][0].texture; U.b2.value = blooms[2][0].texture; U.streak.value = streakA.texture;
    U.uZoom.value = q < 2 ? inFlight * inFlight * 0.035 : 0; U.uTilt.value = 1; U.uExpo.value = fade; U.uTime.value = sec % 10; U.uTint.value.copy(tintNow); U.uBloom.value = 1;
    pass(compMat, null);
  }
  function NIGHTNESS() { return world.uniforms.uNight.value; }
  requestAnimationFrame(frame);
}
