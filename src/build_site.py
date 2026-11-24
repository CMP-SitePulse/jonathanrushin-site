"""Generate the GitHub Pages repo contents (../jr-repo) from index.html.

index.html stays the artifact source (no doctype/html/head/body). This wraps it
in a full document with SEO/social meta, copies photos/, and writes the Pages
support files. It never touches jr-repo/.git and never commits.

Usage: python3 -I build_site.py   (run build_images.sh first if photos changed)
"""
import os
import re
import shutil
import struct
import sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
IN_REPO = os.path.basename(HERE) == "src"  # script lives in <repo>/src
REPO = os.path.normpath(os.path.join(HERE, "..")) if IN_REPO else os.path.normpath(os.path.join(HERE, "..", "jr-repo"))
PHOTOS = os.path.join(REPO, "photos") if IN_REPO else os.path.join(HERE, "photos")
DOMAIN = "jonathanrushin.com"
SITE = "https://" + DOMAIN + "/"

TITLE = "Jonathan Rushin | Chef"
DESCRIPTION = (
    "Jonathan Rushin is an Escoffier-trained private chef cooking Southern and "
    "Mediterranean dinners and events on the Texas Gulf Coast, in Austin, and beyond."
)
OG_IMAGE = SITE + "photos/hero.jpg"  # width/height read from the built file
OG_IMAGE_ALT = "A large commercial fishing vessel tied up at a dock under a blue sky"
# Dark tokens from index.html: --util-bg (top bar) in light and dark themes,
# --char-1 for the favicon tile, --accent (brick red) for the monogram.
THEME_LIGHT = "#1A1615"
THEME_DARK = "#0F0D0C"
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="8" fill="#1C1716"/>'
    '<text x="32" y="45" text-anchor="middle" font-family="Arial Narrow,Arial,sans-serif" '
    'font-size="34" font-weight="700" letter-spacing="-1" fill="#B33224">JR</text></svg>'
)
FAVICON = "data:image/svg+xml," + quote(FAVICON_SVG, safe="=:/,")


def fail(msg):
    sys.exit("build_site: " + msg)


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def split_source(src):
    """Return (head_assets, body) from the artifact source.

    Drops the artifact-only <title> and claude:viewport-fit-sides meta, moves the
    font links and the inline <style> into <head>, and keeps the rest as body.
    """
    lines = src.splitlines(keepends=True)
    kept = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("<title>") or 'name="claude:viewport-fit-sides"' in s:
            continue
        kept.append(ln)
    text = "".join(kept)
    end = text.find("</style>")
    if end < 0:
        fail("no </style> in source")
    end += len("</style>")
    head_assets, body = text[:end].strip(), text[end:].strip()
    if not head_assets.startswith("<link"):
        fail("expected the Google Fonts links at the top of the source")
    return head_assets, body


def strip_comments(head_assets, body):
    """Drop authoring notes from the public page: every HTML comment (the
    <!-- EDIT: ... --> reminders stay in the source only) and every CSS block
    comment inside the <style> element. Script comments are left alone."""
    body = re.sub(r"[ \t]*<!--.*?-->[ \t]*\n?", "", body, flags=re.S)
    if "<!--" in body:
        fail("unterminated HTML comment in source")

    def css(m):
        inner = re.sub(r"^[ \t]*/\*.*?\*/[ \t]*\n", "", m.group(2), flags=re.S | re.M)
        inner = re.sub(r"/\*.*?\*/", "", inner, flags=re.S)
        inner = re.sub(r"[ \t]+\n", "\n", inner)
        inner = re.sub(r"\n{3,}", "\n\n", inner).strip("\n")
        return m.group(1) + "\n" + inner + "\n" + m.group(3)

    head_assets, n = re.subn(r"(<style>)(.*?)(</style>)", css, head_assets, flags=re.S)
    if n != 1:
        fail("expected exactly one <style> in the source head")
    return head_assets, body


def jpeg_size(path):
    """(width, height) from a JPEG SOF marker."""
    with open(path, "rb") as fh:
        data = fh.read()
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    fail("no SOF marker in " + path)


def webp_size(path):
    """(width, height) from a WebP header (VP8, VP8L or VP8X)."""
    with open(path, "rb") as fh:
        d = fh.read(30)
    if d[:4] != b"RIFF" or d[8:12] != b"WEBP":
        fail("not a WebP file: " + path)
    kind = d[12:16]
    if kind == b"VP8 ":
        w, h = struct.unpack("<HH", d[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if kind == b"VP8L":
        b = int.from_bytes(d[21:25], "little")
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    if kind == b"VP8X":
        return int.from_bytes(d[24:27], "little") + 1, int.from_bytes(d[27:30], "little") + 1
    fail("unknown WebP chunk in " + path)


def check_pictures(body, photos):
    """Every <source srcset> entry must name a real file with its real width,
    and every <img> width/height must match its JPEG fallback's aspect ratio
    (so the reserved box is right before the image loads)."""
    n = 0
    for m in re.finditer(r"<picture>(.*?)</picture>", body, flags=re.S):
        block = m.group(1)
        for srcset in re.findall(r'srcset="([^"]*)"', block):
            for item in srcset.split(","):
                url, desc = item.split()
                path = os.path.join(photos, os.path.basename(url))
                if not os.path.isfile(path):
                    fail("srcset names a missing file: " + url)
                real = webp_size(path)[0]
                if desc != "%dw" % real:
                    fail("srcset says %s for %s, file is %dw" % (desc, url, real))
        img = re.search(r'<img src="photos/([^"]+)" width="(\d+)" height="(\d+)"', block)
        if not img:
            fail("picture without <img src width height>: " + block[:80])
        w, h = jpeg_size(os.path.join(photos, img.group(1)))
        aw, ah = int(img.group(2)), int(img.group(3))
        if abs(aw / ah - w / h) > 0.005:
            fail("%s: width/height %dx%d but the file is %dx%d" % (img.group(1), aw, ah, w, h))
        n += 1
    if n == 0:
        fail("no <picture> elements found")
    return n


def page(src):
    head_assets, body = split_source(src)
    head_assets, body = strip_comments(head_assets, body)
    og_w, og_h = jpeg_size(os.path.join(PHOTOS, "hero.jpg"))
    d, t = esc(DESCRIPTION), esc(TITLE)
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        "<title>" + t + "</title>",
        '<meta name="description" content="' + d + '">',
        '<link rel="canonical" href="' + SITE + '">',
        '<meta property="og:type" content="website">',
        '<meta property="og:url" content="' + SITE + '">',
        '<meta property="og:site_name" content="Jonathan Rushin">',
        '<meta property="og:title" content="' + t + '">',
        '<meta property="og:description" content="' + d + '">',
        '<meta property="og:image" content="' + OG_IMAGE + '">',
        '<meta property="og:image:width" content="%d">' % og_w,
        '<meta property="og:image:height" content="%d">' % og_h,
        '<meta property="og:image:alt" content="' + esc(OG_IMAGE_ALT) + '">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="' + t + '">',
        '<meta name="twitter:description" content="' + d + '">',
        '<meta name="twitter:image" content="' + OG_IMAGE + '">',
        '<meta name="theme-color" content="' + THEME_LIGHT + '" media="(prefers-color-scheme: light)">',
        '<meta name="theme-color" content="' + THEME_DARK + '" media="(prefers-color-scheme: dark)">',
        '<link rel="icon" type="image/svg+xml" href="' + FAVICON + '">',
        head_assets,
    ]
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        + "\n".join(head)
        + "\n</head>\n<body>\n"
        + body
        + "\n</body>\n</html>\n"
    )


NOT_FOUND = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found | Jonathan Rushin</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/svg+xml" href="%(favicon)s">
<style>
:root { --bg: #1C1716; --ink: #FFFFFF; --soft: #C9C1BB; --accent: #D2543F; color-scheme: dark; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: var(--bg); color: var(--ink);
  font: 16px/1.6 "Helvetica Neue", Arial, sans-serif; padding: 24px 16px; box-sizing: border-box; }
main { max-width: 32rem; border-left: 3px solid var(--accent); padding-left: 18px; }
h1 { margin: 0 0 8px; font: 800 2.4rem/1 "Arial Narrow", Impact, sans-serif; text-transform: uppercase; }
p { margin: 0 0 18px; color: var(--soft); }
a { color: var(--ink); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; font-size: 14px; }
a:hover { color: var(--accent); }
</style>
</head>
<body>
<main>
<h1>Page not found</h1>
<p>That page is not on the menu.</p>
<a href="/">Back to jonathanrushin.com</a>
</main>
</body>
</html>
""" % {"favicon": FAVICON}

ROBOTS = "User-agent: *\nAllow: /\n\nSitemap: " + SITE + "sitemap.xml\n"

SITEMAP = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    "  <url><loc>" + SITE + "</loc></url>\n"
    "</urlset>\n"
)

README = """# jonathanrushin.com

Personal site for Jonathan Rushin, private chef: one static page served by GitHub Pages from this repo (no build step on GitHub).

Generated files: index.html and photos/ are build output. The editable source page (with EDIT comments marking what to personalize) and the two build scripts live in src/. Edit src/index.html, then run `python3 -I src/build_site.py` from anywhere; it rewrites index.html, README.md and the support files. Original photos are not in the repo; drop them in src/photos-src/ and run `bash src/build_images.sh` only if the photos change.

- Rebuild: `bash src/build_images.sh` (original photos -> photos/: WebP 800/1600 and a JPEG fallback up to 1200 wide, all metadata stripped), then `python3 -I src/build_site.py` (writes this repo). Commit and push; Pages redeploys in a minute or two.
- Change a photo: replace the original for that slot (keep the slot prefix, e.g. gallery-2-*.jpg) and rerun both scripts.
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
"""


def write(name, content):
    with open(os.path.join(REPO, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def main():
    if not os.path.isdir(os.path.join(REPO, ".git")):
        fail("expected an initialised git repo at " + REPO)
    photos = PHOTOS
    if not os.path.isdir(photos) or not os.listdir(photos):
        fail("photos/ is empty; run build_images.sh first")
    with open(os.path.join(HERE, "index.html"), encoding="utf-8") as fh:
        src = fh.read()

    html = page(src)
    for tag in ("<style>", "</style>", "<script>", "</script>", "<h1", "<main", "<body>", "</html>"):
        if html.count(tag) != 1:
            fail("expected exactly one %s in the built page, found %d" % (tag, html.count(tag)))
    if html.find("</style>") > html.find("</head>") or html.find("<script>") < html.find("<body>"):
        fail("style must land in <head> and script in <body>")
    if "<!--" in html:
        fail("HTML comment left in the built page")
    print("pictures checked:", check_pictures(html, photos))
    for out in (html, NOT_FOUND, README):
        try:
            out.encode("ascii")
        except UnicodeEncodeError as e:
            fail("non-ASCII in generated output: " + str(e))

    write("index.html", html)
    write("404.html", NOT_FOUND)
    write("CNAME", DOMAIN)
    write(".nojekyll", "")
    write("robots.txt", ROBOTS)
    write("sitemap.xml", SITEMAP)
    write("README.md", README)
    write(".gitignore", ".DS_Store\n")

    dst = os.path.join(REPO, "photos")
    if os.path.normpath(photos) != os.path.normpath(dst):
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(photos, dst, ignore=shutil.ignore_patterns(".*"))

    for name in sorted(os.listdir(REPO)):
        if name == ".git":
            continue
        p = os.path.join(REPO, name)
        size = sum(os.path.getsize(os.path.join(p, f)) for f in os.listdir(p)) if os.path.isdir(p) else os.path.getsize(p)
        print("%-12s %8d bytes" % (name, size))


if __name__ == "__main__":
    main()
