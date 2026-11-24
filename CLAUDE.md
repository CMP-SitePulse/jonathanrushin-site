# CLAUDE.md

## What this is
The personal site for chef Jonathan Rushin at https://jonathanrushin.com. One static page, served by GitHub Pages from the main branch, repo root. No backend, no framework, no build step on GitHub. The contact form is a mailto: link to rushin97@gmail.com.

## How to make a change
1. Edit `src/index.html` only. The root `index.html`, `404.html`, `CNAME`, `robots.txt`, `sitemap.xml`, `.gitignore` and `README.md` are all generated and get overwritten.
2. `README.md` is generated from the `README` constant in `src/build_site.py`. To change the README, edit that constant, never the file.
3. Run `python3 -I src/build_site.py` from the repo root. It must end with the file size listing and no `build_site:` error.
4. If the build fails, read the message and fix the cause (usually a photo name or size in a `<picture>`). Never bypass or weaken a check.
5. Show the owner what changed in plain words, then commit and push to main. Pages redeploys in about a minute.
6. Give him the live URL, https://jonathanrushin.com, and ask him to refresh it.
`<!-- EDIT: -->` comments in `src/index.html` mark copy still waiting on Jonathan. They never reach the public page.

## Content rules
Verified facts, and the only ones you may state without Jonathan saying so in the conversation:
- Escoffier, class of 2016.
- Formerly Kitchen Manager and Chef at The Rotten Bunch Wine Bar + Kitchen, Austin.
- About six years aboard a commercial fishing vessel in Alaska; Chief Steward since 2023.
- Early years in New York; raised in Ingleside, Texas. Do not state a birthplace.
- Tagline: "Process. Progress. Proceed."
- Contact: rushin97@gmail.com, 361.332.3444. Instagram @j_rushin, plus his Facebook link.
Never invent awards, press, quotes, reviews, employers, boat names, cities, prices or numbers. Anything new must come from Jonathan in the chat. If he asks for copy you cannot back with his own words, write a draft, mark the guesses, and ask him.

## Design rules
- It must not look AI-generated: no gradient heroes, no glow, no glassmorphism, no emoji, no icon grids, no centered-everything layouts, no rounded-card grids.
- Palette: charred black, cast iron, white, and one brick red. Do not add colors.
- Fonts: Barlow Condensed (headings) and Poppins (body), from Google Fonts. Do not add fonts.
- The desktop layout is finished. Mobile has its own rules in the media queries at the end of the `<style>` block (the "phone and tablet layout" section). Change mobile there, and check that a change does not move desktop.

## Photos
- Slots: hero, portrait, service-dining, service-events, gallery-1 to gallery-6. Gallery-5 reads from `gallery-5-*.jpg`, or `spare-sandwich-*.jpg` when there is none (see SLOTS and SKIP in `src/build_images.py`).
- Originals live in `src/photos-src/` (gitignored) as JPEG or PNG, named `<slot>-<anything>.jpg`, one per slot. HEIC cannot be read; ask for a JPEG.
- Build: `python3 src/build_images.py`, then `python3 -I src/build_site.py`. If Pillow is missing, run `python3 -m pip install --user pillow` first. The image build strips all metadata and turns phone photos upright.
- portrait-2 is the hidden second portrait, stacked over portrait: a sideways swipe or drag, or the left/right arrow keys, toggle it. No visible UI (dots, arrows, hint) by design.
- Hero is a landscape crop. The others use object-fit: cover, so keep the subject near the middle.
- If a new photo has a different shape, update that `<img>` width and height in `src/index.html`; the build checks them.
- Never commit `src/photos-src/` or any original photo. Only the built files in `photos/` go in the repo.
New photo from Jonathan (he is on his phone):
1. Ask him to attach the photo in this chat. If you can save the attachment into the repo, put it in `src/photos-src/` as `<slot>-<short-name>.jpg`.
2. If the attachment cannot be saved into the repo, ask him to upload it on github.com in his phone browser: open the repo, tap the `incoming` folder, then Add file > Upload files, pick the photo, and tap Commit changes. If he cannot see Add file, he switches the browser to desktop-site mode (Safari: the aA button > Request Desktop Website). Then `git pull`.
3. Move the file from `incoming/` to `src/photos-src/`, renamed `<slot>-<short-name>.jpg`, and remove the old original for that slot.
4. Run both builds, delete the `incoming/` copy, and commit (the deletion, the new `photos/` files, any `<img>` size change). `incoming/` is not gitignored on purpose; it must be committed for you to see it. Keep `incoming/README.md` so the folder exists; nothing else should stay in it after a photo change.
5. Note: the original stays only in this session's `src/photos-src/`. If a later session needs it, ask him to upload it again.

## Deploy and DNS facts
| Item | Value |
|------|-------|
| Live site | https://jonathanrushin.com (Enforce HTTPS on) |
| Hosting | GitHub Pages, branch main, folder / (root) |
| CNAME file | jonathanrushin.com |
| Domain registrar and DNS | GoDaddy (Marcus's account until moved to Jonathan's) |
| A @ | 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 |
| CNAME www | `<repo owner>.github.io`, lowercase (cmp-sitepulse.github.io before the transfer) |
| Domain renewal | about $23 a year, next renewal February 2028 |
The ownership move is written up step by step in `HANDOFF.md`.

## What NOT to do
- No analytics, cookies, trackers, chat widgets or other third-party scripts. The only outside requests are Google Fonts, plus plain links to his Instagram and Facebook.
- No frameworks, package managers or build tools beyond python3 and Pillow.
- Never hand-edit the root `index.html` or `README.md`.
- Never commit original photos or anything with metadata still in it.
- Never put passwords, tokens, account numbers, or the owner's other accounts (GoDaddy, email, social logins) in the repo.
- Never create accounts or type passwords for the owner.

## Who the owner is and how to talk to him
- While the repo is under CMP-SitePulse, the owner is Jonathan, working through his cousin Marcus Gilmore. After the transfer to Jonathan's GitHub account, the owner is Jonathan alone.
- Jonathan is a chef, not a programmer. Use plain English. Do not show him code or commands unless he asks.
- He only ever works from his phone: the Claude iOS app (Code tab) or a phone browser. Never ask him to use a laptop, a terminal or a desktop app. Any step on github.com or GoDaddy happens in his phone browser or the GoDaddy app.
- Before pushing anything that changes what the site says about his career, cooking or background, show him the exact new wording and wait for a yes.
- Small factual swaps he dictated (phone, email, guest count) can go straight out, then tell him what changed.
- After every deploy, give him https://jonathanrushin.com and tell him what to look for.
