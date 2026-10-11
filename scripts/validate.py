#!/usr/bin/env python3
"""Check every screensaver in screensavers/<id>/ and build index.json.

A screensaver is a folder with saver.json (name, blurb, author, license …), an index.html that runs on its own, a
preview image, and optionally an assets/ folder. Shell:B installs it as a Screensaver project and shows index.html full
screen in a sandboxed iframe (scripts only: no same-origin, no network beyond the project's own files), so the checks
here are about keeping that promise and about running for hours: no external URLs, no audio, no fetch/sockets, sane
sizes. Standard library only; run from the repository root:

    python3 -I scripts/validate.py          # check + rebuild index.json
    python3 -I scripts/validate.py --check  # check only (CI); exits 1 on any error
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAVERS = ROOT / "screensavers"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")
ALLOWED = {".html", ".css", ".js", ".json", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".woff2", ".txt", ".md"}
MAX_FILE, MAX_FOLDER, MAX_PREVIEW = 2 * 2**20, 8 * 2**20, 400 * 2**10
EXTERNAL = re.compile(r"""(?:src|href|url\(|@import\s+)\s*=?\s*['"(]?\s*(https?:)?//""", re.I)
BANNED = (
    (re.compile(r"\bfetch\s*\(", re.I), "fetch(): a screensaver loads nothing"),
    (re.compile(r"\bXMLHttpRequest\b"), "XMLHttpRequest: a screensaver loads nothing"),
    (re.compile(r"\bWebSocket\b|\bEventSource\b"), "sockets: a screensaver talks to nothing"),
    (re.compile(r"<audio\b|\bAudioContext\b|webkitAudioContext", re.I), "audio: screensavers are silent"),
    (re.compile(r"\bnavigator\.(geolocation|mediaDevices|clipboard)\b"), "device APIs are off limits"),
    (re.compile(r"<script[^>]+src\s*=\s*['\"]\s*(https?:)?//", re.I), "external scripts: bundle everything in the folder"),
)


def check(folder: Path) -> tuple[dict | None, list[str], list[str]]:
    errors, warnings = [], []
    sid = folder.name
    if not ID_RE.match(sid):
        errors.append(f"folder name {sid!r}: lowercase letters, digits and dashes only")
    meta_path = folder / "saver.json"
    if not meta_path.is_file():
        return None, ["no saver.json"], []
    try:
        meta = json.loads(meta_path.read_text())
    except ValueError as e:
        return None, [f"saver.json is not valid JSON: {e}"], []
    if not isinstance(meta, dict):
        return None, ["saver.json must hold one object"], []
    if meta.get("id") not in (None, sid):
        errors.append(f"id {meta.get('id')!r} doesn't match the folder name {sid!r}")
    name = str(meta.get("name") or "").strip()
    if not name or len(name) > 40:
        errors.append("name: 1-40 characters")
    if len(str(meta.get("blurb") or "")) > 200:
        errors.append("blurb: at most 200 characters")
    if not meta.get("blurb"):
        warnings.append("no blurb; the picker shows only the name")
    for key in ("author", "license"):
        if not meta.get(key):
            errors.append(f"{key} is required (license: an SPDX id such as MIT or CC0-1.0)")
    if meta.get("tags") is not None and not (isinstance(meta["tags"], list) and all(isinstance(t, str) for t in meta["tags"])):
        errors.append("tags must be a list of strings")
    if meta.get("clockSafe") not in (None, True, False):
        errors.append("clockSafe must be true or false")

    html = folder / "index.html"
    if not html.is_file():
        errors.append("no index.html")
    else:
        text = html.read_text(errors="replace")
        if "<!doctype html>" not in text.lower()[:200]:
            warnings.append("index.html should start with <!doctype html>")
        if EXTERNAL.search(text):
            errors.append("index.html references an external URL (http://, https:// or //); bundle every file in the folder")
        for rx, why in BANNED:
            if rx.search(text):
                errors.append(f"index.html: {why}")
        if "prefers-reduced-motion" not in text:
            warnings.append("index.html doesn't check prefers-reduced-motion (slow down, don't stop)")
        if "resize" not in text:
            warnings.append("index.html doesn't handle resize")
    preview = next((p for p in (folder / "preview.jpg", folder / "preview.png", folder / "preview.webp") if p.is_file()), None)
    if not preview:
        errors.append("no preview.jpg, preview.png or preview.webp (1280×720 or 640×360 of the first seconds)")
    elif preview.stat().st_size > MAX_PREVIEW:
        errors.append(f"{preview.name} is over {MAX_PREVIEW // 1024} KB; save it as a JPEG around 640×360")

    total = 0
    for p in folder.rglob("*"):
        if p.is_symlink():
            errors.append(f"{p.relative_to(folder)}: symbolic links aren't allowed")
            continue
        if not p.is_file():
            continue
        rel = p.relative_to(folder)
        if any(part.startswith(".") for part in rel.parts):
            errors.append(f"{rel}: hidden files aren't allowed")
        if p.suffix.lower() not in ALLOWED and p.name != "saver.json":
            errors.append(f"{rel}: file type {p.suffix or '(none)'} isn't allowed ({', '.join(sorted(ALLOWED))})")
        if p.stat().st_size > MAX_FILE:
            errors.append(f"{rel} is over {MAX_FILE // 2**20} MB")
        total += p.stat().st_size
    if total > MAX_FOLDER:
        errors.append(f"the folder is over {MAX_FOLDER // 2**20} MB in all")
    for k in meta:
        if k not in ("id", "name", "blurb", "author", "license", "version", "tags", "homepage", "clockSafe", "credits"):
            warnings.append(f"saver.json: unknown key {k!r} is ignored")
    return meta, errors, warnings


def main() -> int:
    check_only = "--check" in sys.argv
    index, bad = [], 0
    for folder in sorted(p for p in SAVERS.iterdir() if p.is_dir()):
        meta, errors, warnings = check(folder)
        for w in warnings:
            print(f"  {folder.name}: warning: {w}")
        for e in errors:
            print(f"  {folder.name}: ERROR: {e}")
        if errors or meta is None:
            bad += 1
            continue
        preview = next(p for p in (folder / "preview.jpg", folder / "preview.png", folder / "preview.webp") if p.is_file())
        files = sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file() and p.name != "saver.json" and p != preview)
        index.append({
            "id": folder.name, "name": meta["name"], "blurb": meta.get("blurb", ""), "author": meta.get("author", ""),
            "license": meta.get("license", ""), "version": meta.get("version", "1.0"), "tags": meta.get("tags", []),
            "clockSafe": meta.get("clockSafe", True), "path": f"screensavers/{folder.name}",
            "preview": f"screensavers/{folder.name}/{preview.name}", "files": files,
        })
    if not check_only:
        (ROOT / "index.json").write_text(json.dumps({"format": 1, "kind": "screensaver", "items": index}, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(index)} screensaver{'s' if len(index) != 1 else ''} ok, {bad} with errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
