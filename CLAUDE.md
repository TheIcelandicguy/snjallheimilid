# Snjallheimilið (heimasíða)

Public home page of Snjallheimilið (Davíð, Akureyri): one static page, Icelandic, phone first, GitHub Pages.
Source is this repo on `E:\snjallheimilid` (repo `TheIcelandicguy/snjallheimilid`, public). Nothing goes to `Z:`;
deploy = push to `main`; Pages serves the root at https://snjallheimilið.is (`CNAME` file holds the punycode form xn--snjallheimili-gkb.is, links use it too; the domain was registered
at ISNIC on 2026-11-02, DNS: A/AAAA records of GitHub Pages on the apex, CNAME `www` and `aetlun` to
theicelandicguy.github.io). The estimate page lives in the private `smart-home-estimator` repo, served as
https://aetlun.snjallheimilið.is (aetlun.xn--snjallheimili-gkb.is).

## Layout
- `index.html` — the page: sticky header with anchors, hero with the call to action over a still plan drawing (an inline SVG `.intro`, the film's house of 14 × 10 m on 600 × 440 plan px with Icelandic room names and its wiring, not a real house, a watermark behind the text since owner 2026-11-04, no animation; written by `tools/intro.py` into index.html and site.css, so edit the script and rerun it, not the SVG); the hero's "Hvernig virkar
  þetta?" button goes to `#dagur`), `#dagur` ("Einn dagur í snjallheimili": the film from `tools/film/` as `video/einn-dagur.mp4`, poster `img/einn-dagur.jpg`, captions and clock burned in; owner 2026-11-04 replaced the 3D player with it. site.js plays it muted while it is on screen; the dots `[data-go]` hold each scene's start in seconds, taken from the film's timeline, and `[data-play]` stops and starts it; reduced motion waits to be asked; under 700 px the words in the picture are too small, so `.dline` under it shows the same lines, read from `tools/film/timeline.json`), sections `#thjonusta`
  (four cards), `#vorur` ("Vörur í boði", owner 2026-11-08: nine tabs, `.vtabs` with `role=tablist`, one panel per category (ljós, dimmun, rofar og tenglar, gluggatjöld, hiti, orka og tafla, skynjarar, LED-borðar, stjórnstöð), the same catalogue as the estimate, no prices; site.js `.vtabs` block adds `.js`, shows one panel and takes arrow keys, without script every panel shows; the texts are drafts for the owner to approve, the es / pl ones are Claude's and not yet read by a native speaker), `#kerfi` ("Kerfin sem við vinnum með", owner 2026-11-09: Shelly, Plejd and Tuya (Zigbee / Wi-Fi, BSEED) as cards with product pictures on white tiles, `.systems` / `.pgrid` / `.pfig`, jpg files in `img/products/<system>/` cut from the owner's catalogue PDFs under `F:\For Claude\Product catalog` (soft masks applied, 360 px); the pictures belong to the manufacturers and shops and are credited in the section's small print), `#ferli` (four numbered steps), `#daemi` (one house, numbers from the owner's own house run through
  quick.html on 2026-11-01: 13 modules, 155–190 þús. kr.), `#um`, `#samband` (contact form, honeypot `_gotcha`).
- `site.css` — same colour tokens as quick.css in smart-home-estimator (light and dark by `prefers-color-scheme`),
  880 px wrap, cards, numbered steps, form.
- `tools/film/` — the Blender remake of the Einn dagur film (owner 2026-11-03, from his reference picture of a new plan), rendered to MP4, on the page as `video/einn-dagur.mp4` (copy of `einn-dagur-blender-lett.mp4` from `E:\motion-tools\out`). `tools/film/house.py` builds the house, `tools/film/film.py` keys the six scenes and renders the frames, `tools/film/hud.py` draws the clock, captions, energy meter and end card and writes the video, `tools/film/timeline.json` holds the texts, clock and energy figures, `tools/film/fetch_assets.py` downloads the CC0 Poly Haven models and textures. `tools/film/energy.json` and the figures in the timeline come from the owner's own house, with his leave; the day in the film is put together from two real days. Assets, frames and videos stay outside git in `E:\motion-tools`. Run with `blender -b --factory-startup --python tools/film/film.py -- --frames DIR`, then `python tools/film/hud.py DIR out.mp4`.
- `site.js` — `AETLUN` = the estimate page's address (aetlun.snjallheimilið.is), set on every `[data-aetlun]` link;
  `FORM` = the Formspree id shared with quick.html, subject
  "Fyrirspurn af snjallheimilið.is"; the form posts JSON and shows the result in `#formMsg`.
  Also the `#dagur` film player (see index.html above). `LANG` is the page's language: index.html is Icelandic; the
  copies `en/index.html`, `es/index.html` and `pl/index.html` set `window.I18N` (lang and the few strings site.js shows), and site.js
  then takes the film and captions of that language and sends the estimate link with `?lang=`.
- Languages (owner 2026-11-04: English, Spanish, Polish): `tools/i18n.py` writes the three copies of index.html from the Icelandic one,
  every text node and text attribute (not svg, script, style) looked up in `i18n/en.json`, `i18n/es.json`, `i18n/pl.json`
  (Icelandic text -> translation; the hero svg's room names and circuit labels, the list in the script, are looked up in the same files); a text without a translation stops the build, `--dump` lists what index.html needs.
  Rerun it after any change to index.html. The header's `.lang` switch and the hreflang links are in index.html by hand.
  The film per language: `tools/film/timeline.en.json` (.es, .pl) carry the scene lines and the HUD's words (`labels`),
  `python tools/film/hud.py FRAMES out.mp4 --lang en` draws them over the same frames (E:\motion-tools\film\langs.sh does the
  three) into `video/einn-dagur.en.mp4` etc.; the 3D frames themselves stay as rendered, so the wall display says
  Allt slökkt in every language. The estimate page has its own tables (quick-i18n.js in smart-home-estimator).
- `fonts/inter.woff2` — Inter, the one typeface of the logo, the site, the estimate page and the film's HUD (self-hosted, OFL, `fonts/inter-LICENSE.txt`). the Latin Extended glyphs (Polish) come from `fonts/inter-latin-ext.woff2` with a unicode-range; `tools/logo/outline.py` turns the text of the owner's logo sources in `tools/logo/src/` into outlines in `img/logo-larett.svg` and `img/logo-hringlaga.svg`, so they look the same without the font; their PNGs are drawn from those. Colours (owner 2026-11-04): the warm palette stays, and `--sky` / `--glass` in `site.css` are the logo's light colours, for lines and fills, not for text on the light ground.
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
