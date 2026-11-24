# jonathanrushin.com

Personal site for Jonathan Rushin, private chef: one static page served by GitHub Pages from this repo (no build step on GitHub).

Generated files: index.html and photos/ are build output. The editable source page (with EDIT comments marking what to personalize) and the two build scripts live in src/. Edit src/index.html, then run `python3 -I src/build_site.py` from anywhere; it rewrites index.html, README.md and the support files. Original photos are not in the repo; drop them in src/photos-src/ and run `python3 src/build_images.py` only if the photos change. The image build needs Pillow: `python3 -m pip install --user pillow`.

- Rebuild: `python3 src/build_images.py` (original photos -> photos/: WebP 800/1600 and a JPEG fallback up to 1200 wide, all metadata stripped), then `python3 -I src/build_site.py` (writes this repo). Commit and push; Pages redeploys in a minute or two.
- Change a photo: replace the original for that slot (keep the slot prefix, e.g. gallery-2-*.jpg) and rerun both scripts. From a phone, upload the photo on github.com into incoming/ and ask Claude to build it in (see CLAUDE.md).
- Small text fix without the source: edit index.html here, then make the same edit in the source page so it survives the next rebuild.

No analytics, cookies or third-party scripts. The only outside requests are Google Fonts. The contact form has no backend: it opens the visitor's email app with a pre-filled message to rushin97@gmail.com.

## Domain

CNAME holds jonathanrushin.com. DNS records at the domain host:

| Type  | Name | Value |
|-------|------|-------|
| A     | @    | 185.199.108.153 |
| A     | @    | 185.199.109.153 |
| A     | @    | 185.199.110.153 |
| A     | @    | 185.199.111.153 |
| CNAME | www  | cmp-sitepulse.github.io |

Then in the repo, Settings > Pages: set the custom domain and tick Enforce HTTPS once the certificate is issued.

Ownership: the repo can be transferred to Jonathan's own GitHub account later (Settings > Transfer). The www CNAME must then point at the new owner's `<user>.github.io`; re-check the Pages domain afterwards.
