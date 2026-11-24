"""Build web derivatives of the slot photos into photos/.

For each slot: WebP at 800w and 1600w (quality 74, method 6, capped at the
source width, never upscaled, no metadata) plus a JPEG fallback at most 1200w
(quality 72, progressive, optimized, no metadata). The JPEG is only for
browsers without WebP and for link previews (og:image = hero.jpg).
Re-runnable: photos/ is rebuilt from scratch.

Runs anywhere python3 and Pillow run (macOS, Linux, Claude Code on the web).
Usage: python3 src/build_images.py
Needs Pillow: python3 -m pip install --user pillow
"""
import io
import math
import os
import shutil
import sys
import tempfile

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("build_images: Pillow is missing. Run: python3 -m pip install --user pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "photos-src")
OUT = os.path.join(HERE, "..", "photos") if os.path.basename(HERE) == "src" else os.path.join(HERE, "photos")
OUT = os.path.normpath(OUT)

WEBP_Q = 74
JPEG_Q = 72
JPEG_MAX = 1200
EXTS = (".jpg", ".jpeg", ".png")

# slot name -> source file prefixes, tried in order. The file is named
# <prefix>-<anything>.<ext> (the Instagram shortcode suffix is dropped).
# gallery-5 falls back to the spare sandwich shot when no gallery-5-* file
# exists.
SLOTS = [
    ("hero", ["hero"]),
    ("portrait", ["portrait"]),
    ("service-dining", ["service-dining"]),
    ("service-events", ["service-events"]),
    ("gallery-1", ["gallery-1"]),
    ("gallery-2", ["gallery-2"]),
    ("gallery-3", ["gallery-3"]),
    ("gallery-4", ["gallery-4"]),
    ("gallery-5", ["gallery-5", "spare-sandwich"]),
    ("gallery-6", ["gallery-6"]),
]
# Originals that must never be used for their slot. The original gallery-5
# Instagram shot is a wheelhouse electronics photo, not food.
SKIP = {"gallery-5-DHMQ6cYyOrq.jpg"}

# Per-slot top crop, as the width:height the kept part must have. The rows
# above it are cut away and the bottom edge stays. service-events: the top of
# the shot is a paper towel and the steel tray wall; on a phone the tall card
# shows exactly that above the text, so it is cut and the fruit and loaves
# fill the card. 1440:1298 is the crop the photo was built with (1440x1794
# source, top 496 rows cut), and src/index.html sizes the card to match.
TOP_CROP = {"service-events": (1440, 1298)}


def fail(msg):
    sys.exit("build_images: " + msg)


def find_source(slot, prefixes, files):
    for prefix in prefixes:
        hits = sorted(
            f for f in files
            if f.startswith(prefix + "-") and f.lower().endswith(EXTS) and f not in SKIP
        )
        if len(hits) > 1:
            print("build_images: %s: several originals, using %s (remove the others): %s"
                  % (slot, hits[0], ", ".join(hits[1:])))
        if hits:
            return hits[0]
    heic = [f for f in files if f.lower().endswith((".heic", ".heif"))
            and any(f.startswith(p + "-") for p in prefixes)]
    if heic:
        fail("%s: %s is HEIC, which Pillow cannot read. Save it as JPEG instead "
             "(on the iPhone: Settings > Camera > Formats > Most Compatible, or share it as JPEG)."
             % (slot, heic[0]))
    fail("no original for slot %s in %s (expected %s-*.jpg)" % (slot, SRC, prefixes[0]))


def load(path):
    """Open, apply EXIF orientation, convert to sRGB if a profile is embedded,
    and return a plain RGB image with no metadata attached."""
    with Image.open(path) as im:
        im.load()
        icc = im.info.get("icc_profile")
        im = ImageOps.exif_transpose(im)
    if icc:
        try:
            from PIL import ImageCms
            src_prof = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            dst_prof = ImageCms.createProfile("sRGB")
            mode = "RGB" if im.mode not in ("RGB", "RGBA") else im.mode
            im = ImageCms.profileToProfile(im.convert(mode), src_prof, dst_prof, outputMode=mode)
        except Exception as e:  # unreadable profile: keep the pixels as they are
            print("build_images: %s: colour profile ignored (%s)" % (os.path.basename(path), e))
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        flat = Image.new("RGB", im.size, (255, 255, 255))
        flat.paste(im, mask=im.getchannel("A"))
        im = flat
    else:
        im = im.convert("RGB")
    im.info = {}
    return im


def top_crop(im, aspect):
    w, h = im.size
    keep = round(w * aspect[1] / aspect[0])
    if keep >= h:
        print("build_images: photo is already wider than the %d:%d crop, not cropped" % aspect)
        return im
    return im.crop((0, h - keep, w, h))


def resized(im, width, round_up):
    """Scale to width, keeping the aspect. WebP heights round up and JPEG
    heights round down, matching the files the earlier cwebp/sips build made
    (and the width/height attributes in src/index.html)."""
    sw, sh = im.size
    if width >= sw:
        return im
    exact = sh * width / sw
    height = math.ceil(exact - 1e-9) if round_up else math.floor(exact + 1e-9)
    return im.resize((width, height), Image.LANCZOS)


def strip_jpeg(data):
    """The source JPEG with every APPn (except JFIF APP0 and Adobe APP14) and
    COM marker removed. Lossless: the image data is copied byte for byte."""
    if data[:2] != b"\xff\xd8":
        return None
    out = bytearray(data[:2])
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker == 0xFF:
            i += 1
            continue
        length = int.from_bytes(data[i + 2:i + 4], "big")
        seg = data[i:i + 2 + length]
        if marker == 0xDA:  # start of scan: the rest is image data
            out += data[i:]
            return bytes(out)
        if not ((0xE1 <= marker <= 0xED) or marker == 0xEF or marker == 0xFE):
            out += seg
        i += 2 + length
    return None


def save_webp(im, path):
    im.save(path, "WEBP", quality=WEBP_Q, method=6)


def jpeg_bytes(im):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=JPEG_Q, optimize=True, progressive=True, subsampling="4:2:0")
    return buf.getvalue()


def needs_transform(path):
    """True if the source has an EXIF orientation other than upright, so its
    own bytes would display rotated once the EXIF is stripped."""
    with Image.open(path) as im:
        return im.format != "JPEG" or im.getexif().get(0x0112, 1) != 1


def main():
    if not os.path.isdir(SRC):
        fail("no originals folder at " + SRC)
    files = os.listdir(SRC)
    for f in files:
        if f.lower().endswith((".heic", ".heif")):
            print("build_images: %s is HEIC and is ignored; Pillow cannot read HEIC. Save it as JPEG." % f)
    plan = [(slot, find_source(slot, prefixes, files)) for slot, prefixes in SLOTS]

    tmp = tempfile.mkdtemp(prefix="photos-", dir=os.path.dirname(OUT))
    try:
        for slot, name in plan:
            path = os.path.join(SRC, name)
            im = load(path)
            crop = TOP_CROP.get(slot)
            if crop:
                im = top_crop(im, crop)
            sw = im.size[0]

            # WebP 800 and 1600, never upscaled. If the source is not wider
            # than 800, only the 800 file is written (at source width).
            save_webp(resized(im, min(sw, 800), True), os.path.join(tmp, slot + "-800.webp"))
            if sw > 800:
                save_webp(resized(im, min(sw, 1600), True), os.path.join(tmp, slot + "-1600.webp"))

            # JPEG fallback. If no resize or crop is needed and the re-encode
            # is not smaller than the source, the source is used instead, with
            # its metadata stripped losslessly.
            small = resized(im, min(sw, JPEG_MAX), False)
            enc = jpeg_bytes(small)
            how = "q%d" % JPEG_Q
            if small is im and not crop and not needs_transform(path):
                with open(path, "rb") as fh:
                    orig = strip_jpeg(fh.read())
                if orig and len(enc) >= len(orig):
                    enc, how = orig, "source, stripped"
            with open(os.path.join(tmp, slot + ".jpg"), "wb") as fh:
                fh.write(enc)
            jw, jh = small.size
            print("%s <- %s%s  src %dw %dB  jpg %dx%d %dB (%s)" % (
                slot, name, " top crop %d:%d" % crop if crop else "", sw,
                os.path.getsize(path), jw, jh, len(enc), how))

        shutil.rmtree(OUT, ignore_errors=True)
        os.replace(tmp, OUT)
        os.chmod(OUT, 0o755)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    sizes = [os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)]
    print("total: %.1f MB  (%d files, %d bytes)" % (sum(sizes) / 1e6, len(sizes), sum(sizes)))


if __name__ == "__main__":
    main()
