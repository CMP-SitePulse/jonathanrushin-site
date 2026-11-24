#!/bin/bash
# Build web derivatives of the slot photos into photos/.
# For each slot: WebP at 800w and 1600w (q74, method 6, capped at source width,
# no metadata) plus a JPEG fallback at most 1200w (q72, no metadata). The JPEG
# is only for browsers without WebP and for link previews (og:image = hero.jpg).
# Re-runnable: photos/ is rebuilt from scratch.
# Usage: bash build_images.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/photos-src"
OUT="$HERE/photos"
if [ "$(basename "$HERE")" = "src" ]; then OUT="$HERE/../photos"; fi
BIN="${BIN:-/opt/homebrew/bin}"
CWEBP="${CWEBP:-$BIN/cwebp}"
CJPEG="${CJPEG:-$BIN/cjpeg}"
DJPEG="${DJPEG:-$BIN/djpeg}"
JPEGTRAN="${JPEGTRAN:-$BIN/jpegtran}"
WEBP_Q=74
JPEG_Q=72
JPEG_MAX=1200

# slot name -> source file prefix (the Instagram shortcode suffix is dropped).
# gallery-5 uses the spare sandwich shot: the original gallery-5 source is a
# wheelhouse electronics photo, not food.
SLOTS="
hero:hero
portrait:portrait
service-dining:service-dining
service-events:service-events
gallery-1:gallery-1
gallery-2:gallery-2
gallery-3:gallery-3
gallery-4:gallery-4
gallery-5:spare-sandwich
gallery-6:gallery-6
"

size() { stat -f %z "$1"; }

rm -rf "$OUT"
mkdir -p "$OUT"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

for pair in $SLOTS; do
  slot="${pair%%:*}"
  prefix="${pair#*:}"
  src="$(ls "$SRC/$prefix"-*.jpg | head -n 1)"
  orig="$src"

  # Optional per-slot crop, done losslessly by jpegtran (offsets on the 16px
  # MCU grid). service-events: the top quarter of the shot is a paper towel
  # and the steel tray wall; on a phone the tall card shows exactly that above
  # the text, so it is cut away and the fruit and loaves fill the card.
  crop=""
  case "$slot" in
    service-events) crop="1440x1298+0+496" ;;
  esac
  if [ -n "$crop" ]; then
    "$JPEGTRAN" -copy none -crop "$crop" -outfile "$tmpdir/crop.jpg" "$src"
    src="$tmpdir/crop.jpg"
  fi
  sw="$(sips -g pixelWidth "$src" | awk '/pixelWidth/ {print $2}')"

  # WebP 800 and 1600, never upscaled. If the source is not wider than 800,
  # only the 800 file is written (at source width).
  w800=$(( sw < 800 ? sw : 800 ))
  "$CWEBP" -quiet -q "$WEBP_Q" -m 6 -metadata none -resize "$w800" 0 "$src" -o "$OUT/$slot-800.webp"
  if [ "$sw" -gt 800 ]; then
    w1600=$(( sw < 1600 ? sw : 1600 ))
    "$CWEBP" -quiet -q "$WEBP_Q" -m 6 -metadata none -resize "$w1600" 0 "$src" -o "$OUT/$slot-1600.webp"
  fi

  # JPEG fallback. sips only resamples (its JPEG quality setting is unreliable
  # and it carries the source XMP/IPTC over), so it writes a near-lossless
  # intermediate that libjpeg-turbo re-encodes at JPEG_Q. cjpeg writes no
  # metadata. If the re-encode is not smaller than the source, the source is
  # used instead, stripped of every marker by jpegtran -copy none.
  if [ "$sw" -gt "$JPEG_MAX" ]; then
    sips -s format jpeg -s formatOptions best --resampleWidth "$JPEG_MAX" "$src" --out "$tmpdir/r.jpg" >/dev/null
    in="$tmpdir/r.jpg"
  else
    in="$src"
  fi
  "$DJPEG" -pnm "$in" | "$CJPEG" -quality "$JPEG_Q" -optimize -progressive -outfile "$tmpdir/enc.jpg"
  "$JPEGTRAN" -copy none -optimize -progressive -outfile "$tmpdir/orig.jpg" "$src"
  how="q$JPEG_Q"
  if [ "$(size "$tmpdir/enc.jpg")" -ge "$(size "$tmpdir/orig.jpg")" ]; then
    cp "$tmpdir/orig.jpg" "$OUT/$slot.jpg"
    how="source, stripped"
  else
    cp "$tmpdir/enc.jpg" "$OUT/$slot.jpg"
  fi
  jw="$(sips -g pixelWidth "$OUT/$slot.jpg" | awk '/pixelWidth/ {print $2}')"
  jh="$(sips -g pixelHeight "$OUT/$slot.jpg" | awk '/pixelHeight/ {print $2}')"
  echo "$slot <- $(basename "$orig")${crop:+ crop $crop}  src ${sw}w $(size "$src")B  jpg ${jw}x${jh} $(size "$OUT/$slot.jpg")B ($how)"
done

echo "total: $(du -sh "$OUT" | cut -f1)  ($(find "$OUT" -type f | wc -l | tr -d ' ') files, $(find "$OUT" -type f -exec stat -f %z {} + | awk '{s+=$1} END {print s}') bytes)"
