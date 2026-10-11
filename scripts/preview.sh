#!/usr/bin/env bash
# preview.sh screensavers/<id> — screenshot index.html with headless Firefox (1280×720) and save it as preview.jpg.
# Needs firefox on PATH (or FIREFOX=/path/to/firefox) and, to make the JPEG, Python with Pillow; without Pillow the
# PNG is kept as preview.png.
set -e
dir=$(cd "$1" && pwd)
ff=${FIREFOX:-$(command -v firefox || echo /snap/bin/firefox)}
# A snap-confined Firefox can only write under its own folder or to plain (non-hidden) paths in $HOME, so the
# screenshot and the throwaway profile go there; override with PREVIEW_TMP.
if [ -z "$PREVIEW_TMP" ] && [ -d "$HOME/snap/firefox/common" ]; then base=$HOME/snap/firefox/common/tmp; else base=${PREVIEW_TMP:-$HOME/shellb-preview-tmp}; fi
mkdir -p "$base"
prof=$(mktemp -d -p "$base")
tmp=$(mktemp -d -p "$base")
timeout 60 "$ff" --headless --no-remote --profile "$prof" --window-size=1280,720 --screenshot "$tmp/shot.png" "file://$dir/index.html" >/dev/null 2>&1 || true
rm -rf "$prof"
[ -s "$tmp/shot.png" ] || { echo "no screenshot produced"; exit 1; }
if python3 -c "import PIL" 2>/dev/null; then
  python3 - "$tmp/shot.png" "$dir/preview.jpg" <<'PY'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
im.thumbnail((640, 360))
im.save(sys.argv[2], "JPEG", quality=82, optimize=True)
PY
  rm -f "$dir/preview.png"
else
  mv "$tmp/shot.png" "$dir/preview.png"
fi
rm -rf "$tmp"
ls -la "$dir"/preview.*
