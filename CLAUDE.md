# Snjallheimilið (heimasíða)

Public home page of Snjallheimilið (Davíð, Akureyri): one static page, Icelandic, phone first, GitHub Pages.
Source is this repo on `E:\snjallheimilid` (repo `TheIcelandicguy/snjallheimilid`, public). Nothing goes to `Z:`;
deploy = push to `main`; Pages serves the root at https://snjallheimilið.is (`CNAME` file holds the punycode form xn--snjallheimili-gkb.is, links use it too; the domain was registered
at ISNIC on 2026-11-02, DNS: A/AAAA records of GitHub Pages on the apex, CNAME `www` and `aetlun` to
theicelandicguy.github.io). The estimate page lives in the private `smart-home-estimator` repo, served as
https://aetlun.snjallheimilið.is (aetlun.xn--snjallheimili-gkb.is).

## Layout
- `index.html` — the page: sticky header with anchors, hero with the call to action and the intro drawing (owner
  2026-11-02: an inline SVG `.intro`, a sample house of 600 × 440 plan px with Icelandic room names, not a real
  house, written by `tools/intro.py` into index.html and site.css, so edit the script and rerun it, not the SVG:
  every stroke has `pathLength="1"`, its start `--d` and duration `--t`; outer wall, inner walls and names,
  windows and doors to 3.5 s, then the electrical layer as a wiring drawing: the run travels from the board T1
  circuit by circuit at a constant speed, Gr.1 lights with a drop to each switch, Gr.2 sockets round the walls,
  the symbols appearing as the line reaches them, to 8.3 s; then the drawing fades to a watermark and the hero
  text comes up at 8.5 s; `prefers-reduced-motion` shows the finished state at once; the hero's "Hvernig virkar
  þetta?" button goes to `#dagur`), `#dagur` (owner 2026-11-03, "Einn dagur í snjallheimili": the same sample house as
  a scene player, seven scenes from the storyboard he settled: 04:50 the alarm with the bathroom and the kitchen's
  under-cabinet light at 10 %, 06:30 the same switch held dims the kitchen ceiling light alone, 08:00 leaving and every
  light goes off in turn plus the iron's socket, 12:00 the board's energy bars, 18:40 curtains, warm living-room light
  and 21 °C, 03:10 a 10 % hallway light and the water sensor's phone notice, then the closing line; the SVG between the
  `<!-- dagur:svg -->` markers and the CSS from `/* Dagur:` are written by `tools/dagur.py` (edit the script and
  rerun it; the optional argument patches the single-file artifact copy), the caption per scene is in `.dcap`, the
  dots `[data-go]` and the `[data-play]` button in `.dots`; site.js sets `data-scene` on `.dagur` and the CSS does
  the rest: per-light level variables, the scene's extras `.sc[data-s]`, small keyframes; auto-advance 4–5 s per
  scene while the section is on screen, a dot stops the run, `prefers-reduced-motion` = dots only; in 3D since
  2026-11-03 (owner: "meira 3D", then "svona 3D" with a furnished dollhouse render as the reference): `dagur3d.js`,
  an ES module importing Three.js 0.160.0 from cdnjs, lays `img/dagur-floor.jpg` on the floor (a top-down furnished
  render of the sample house made with Canva's image generator on 2026-11-03, 1456 × 1088 px, the same five rooms
  as the drawing; the SVG house is painted on the floor only if the image fails), keeps the house in a HOUSE
  table measured in the image's pixels (walls with windows and doors, the front door hinge, the lights, the kitchen
  strip, the bars, the curtain window, the water sensor; another render means re-measuring it), raises the walls as
  half-transparent slabs split at the openings with their edges drawn, a glow sprite and a point light per ceiling light and the strip,
  the front door leaf, the energy bars, the curtain, the water rings and HTML labels projected from world points;
  it watches `data-scene` and flies the camera per scene; without WebGL, reduced motion or no CDN the SVG player
  stays; `.d3` box, `.d3labels`, `.dsvg.d3off` hides the SVG), sections `#thjonusta`
  (four cards), `#ferli` (four numbered steps), `#daemi` (one house, numbers from the owner's own house run through
  quick.html on 2026-11-01: 13 modules, 155–190 þús. kr.), `#um`, `#samband` (contact form, honeypot `_gotcha`).
- `site.css` — same colour tokens as quick.css in smart-home-estimator (light and dark by `prefers-color-scheme`),
  880 px wrap, cards, numbered steps, form.
- `dagur3d.js` — the 3D scene player (see `#dagur` above).
- `site.js` — `AETLUN` = the estimate page's address (aetlun.snjallheimilið.is), set on every `[data-aetlun]` link;
  `FORM` = the Formspree id shared with quick.html, subject
  "Fyrirspurn af snjallheimilið.is"; the form posts JSON and shows the result in `#formMsg`.
  Also the `#dagur` scene player (see index.html above).
- `img/dagur-floor.jpg` — the furnished render of the sample house, the floor of the 3D scene player (Canva, 2026-11-03).
- `favicon.svg`, `.nojekyll` (Pages serves files as they are), `CNAME` (the custom domain for Pages), `README.md`,
  `LICENSE` (MIT for the code only).
- Run: `python -m http.server 8766` here (`.claude/launch.json` has it as `site`).

## Rules
- Text is the owner's voice: draft it, he approves. Never invent prices, certifications or claims about him.
  The electrical work on a house is done by a licensed electrician; the site says so and must keep saying so.
- Icelandic first; English page later, same structure.
- Before ending a session: `python check_docs.py` (paths and ids named here must exist), update this file, commit, push.

## Open
- ON HOLD since 2026-11-02 (owner not ready for leads): Pages serves the orphan branch `hold` (one holding page, no
  form, noindex, plus CNAME and favicon) on the custom domain instead of `main`. To go live: Settings → Pages → source
  branch `main` (or `gh api -X PUT repos/TheIcelandicguy/snjallheimilid/pages` with `{"source":{"branch":"main","path":"/"}}`),
  then delete `hold`. Nothing on `main` changes meanwhile; keep developing there.
- Domain verified under the GitHub account 2026-11-02 (TXT `_github-pages-challenge-TheIcelandicguy` at ISNIC), so
  nobody else can point a Pages site at it; HTTPS is enforced on both sites. The ASCII spelling snjallheimilid.is is
  not registered.
- English version; photos of real installations (none yet); the example section wants a second house.
