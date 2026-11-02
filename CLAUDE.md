# Snjallheimilið (heimasíða)

Public home page of Snjallheimilið (Davíð, Akureyri): one static page, Icelandic, phone first, GitHub Pages.
Source is this repo on `E:\snjallheimilid` (repo `TheIcelandicguy/snjallheimilid`, public). Nothing goes to `Z:`;
deploy = push to `main`, Pages serves the root. Domain `snjallheimilid.is` (owner registers it at ISNIC; then a
`CNAME` file here and the DNS records). The estimate page lives in the private `smart-home-estimator` repo.

## Layout
- `index.html` — the page: sticky header with anchors, hero with the call to action, sections `#thjonusta`
  (four cards), `#ferli` (four numbered steps), `#daemi` (one house, numbers from the owner's own house run through
  quick.html on 2026-11-01: 13 modules, 155–190 þús. kr.), `#um`, `#samband` (contact form, honeypot `_gotcha`).
- `site.css` — same colour tokens as quick.css in smart-home-estimator (light and dark by `prefers-color-scheme`),
  880 px wrap, cards, numbered steps, form.
- `site.js` — `AETLUN` = the estimate page's address, set on every `[data-aetlun]` link (change once when
  `aetlun.snjallheimilid.is` exists); `FORM` = the Formspree id shared with quick.html, subject
  "Fyrirspurn af snjallheimilid.is"; the form posts JSON and shows the result in `#formMsg`.
- `favicon.svg`, `.nojekyll` (Pages serves files as they are), `README.md`, `LICENSE` (MIT for the code only).
- Run: `python -m http.server 8766` here (`.claude/launch.json` has it as `site`).

## Rules
- Text is the owner's voice: draft it, he approves. Never invent prices, certifications or claims about him.
  The electrical work on a house is done by a licensed electrician; the site says so and must keep saying so.
- Icelandic first; English page later, same structure.
- Before ending a session: `python check_docs.py` (paths and ids named here must exist), update this file, commit, push.

## Open
- Domain: register `snjallheimilid.is`, add `CNAME`, DNS A/AAAA records for the apex and `aetlun` CNAME to the
  estimator's Pages. Until then the site is at https://theicelandicguy.github.io/snjallheimilid/.
- English version; photos of real installations (none yet); the example section wants a second house.
