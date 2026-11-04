# Snjallheimilið (heimasíða)

Public home page of Snjallheimilið (Davíð, Akureyri): one static page, Icelandic, phone first, GitHub Pages.
Source is this repo on `E:\snjallheimilid` (repo `TheIcelandicguy/snjallheimilid`, public). Nothing goes to `Z:`;
deploy = push to `main`; Pages serves the root at https://snjallheimilið.is (`CNAME` file holds the punycode form xn--snjallheimili-gkb.is, links use it too; the domain was registered
at ISNIC on 2026-11-02, DNS: A/AAAA records of GitHub Pages on the apex, CNAME `www` and `aetlun` to
theicelandicguy.github.io). The estimate page lives in the private `smart-home-estimator` repo, served as
https://aetlun.snjallheimilið.is (aetlun.xn--snjallheimili-gkb.is).

## Layout
- `index.html` — the page: sticky header with anchors, hero with the call to action and the intro drawing (owner
  2026-11-02: an inline SVG `.intro`, the film's house of 14 × 10 m on 600 × 440 plan px with Icelandic room names, not a real
  house, written by `tools/intro.py` into index.html and site.css, so edit the script and rerun it, not the SVG:
  every stroke has `pathLength="1"`, its start `--d` and duration `--t`; outer wall, inner walls and names,
  windows and doors to 3.5 s, then the electrical layer as a wiring drawing: the run travels from the board T1
  circuit by circuit at a constant speed, Gr.1 lights with a drop to each switch, Gr.2 sockets round the walls,
  the symbols appearing as the line reaches them, to 8.5 s; then the drawing fades to a watermark and the hero
  text comes up at 8.7 s; `prefers-reduced-motion` shows the finished state at once; the hero's "Hvernig virkar
  þetta?" button goes to `#dagur`), `#dagur` ("Einn dagur í snjallheimili": the film from `tools/film/` as `video/einn-dagur.mp4`, poster `img/einn-dagur.jpg`, captions and clock burned in; owner 2026-11-04 replaced the 3D player with it. site.js plays it muted while it is on screen; the dots `[data-go]` hold each scene's start in seconds, taken from the film's timeline, and `[data-play]` stops and starts it; reduced motion waits to be asked; under 700 px the words in the picture are too small, so `.dline` under it shows the same lines, read from `tools/film/timeline.json`), sections `#thjonusta`
  (four cards), `#ferli` (four numbered steps), `#daemi` (one house, numbers from the owner's own house run through
  quick.html on 2026-11-01: 13 modules, 155–190 þús. kr.), `#um`, `#samband` (contact form, honeypot `_gotcha`).
- `site.css` — same colour tokens as quick.css in smart-home-estimator (light and dark by `prefers-color-scheme`),
  880 px wrap, cards, numbered steps, form.
- `tools/film/` — the Blender remake of the Einn dagur film (owner 2026-11-03, from his reference picture of a new plan), rendered to MP4, on the page as `video/einn-dagur.mp4` (copy of `einn-dagur-blender-lett.mp4` from `E:\motion-tools\out`). `tools/film/house.py` builds the house, `tools/film/film.py` keys the six scenes and renders the frames, `tools/film/hud.py` draws the clock, captions, energy meter and end card and writes the video, `tools/film/timeline.json` holds the texts, clock and energy figures, `tools/film/fetch_assets.py` downloads the CC0 Poly Haven models and textures. `tools/film/energy.json` and the figures in the timeline come from the owner's own house, with his leave; the day in the film is put together from two real days. Assets, frames and videos stay outside git in `E:\motion-tools`. Run with `blender -b --factory-startup --python tools/film/film.py -- --frames DIR`, then `python tools/film/hud.py DIR out.mp4`.
- `site.js` — `AETLUN` = the estimate page's address (aetlun.snjallheimilið.is), set on every `[data-aetlun]` link;
  `FORM` = the Formspree id shared with quick.html, subject
  "Fyrirspurn af snjallheimilið.is"; the form posts JSON and shows the result in `#formMsg`.
  Also the `#dagur` film player (see index.html above).
- `fonts/inter.woff2` — Inter, the one typeface of the logo, the site, the estimate page and the film's HUD (self-hosted, OFL, `fonts/inter-LICENSE.txt`). `tools/logo/outline.py` turns the text of the owner's logo sources in `tools/logo/src/` into outlines in `img/logo-larett.svg` and `img/logo-hringlaga.svg`, so they look the same without the font; their PNGs are drawn from those. Colours (owner 2026-11-04): the warm palette stays, and `--sky` / `--glass` in `site.css` are the logo's light colours, for lines and fills, not for text on the light ground.
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
