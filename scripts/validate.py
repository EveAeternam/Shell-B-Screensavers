#!/usr/bin/env python3
"""Check every screensaver in screensavers/<id>/, build index.json and the gallery in README.md.

A screensaver is a folder with saver.json (name, blurb, author, license …), an index.html that runs on its own, a
preview image, and optionally an assets/ folder. Shell:B installs it as a Screensaver project and shows index.html full
screen in a sandboxed iframe (scripts only: no same-origin, no network beyond the project's own files), so the checks
here are about keeping that promise and about running for hours: no external URLs, no audio, no fetch/sockets, sane
sizes. Standard library only; run from the repository root:

    python3 -I scripts/validate.py          # check + rebuild index.json and the README gallery
    python3 -I scripts/validate.py --check  # check only (CI); exits 1 on any error or stale generated file
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAVERS = ROOT / "screensavers"
README = ROOT / "README.md"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")
URL_RE = re.compile(r"^https?://[^\s\"'<>]{1,200}$")
START, END = "<!-- gallery:start -->", "<!-- gallery:end -->"
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
        if not meta.get(key) or not isinstance(meta[key], str):
            errors.append(f"{key} is required (license: an SPDX id such as MIT or CC0-1.0)")
    if isinstance(meta.get("author"), str) and len(meta["author"]) > 80:
        errors.append("author: at most 80 characters")
    for key in ("authorUrl", "homepage"):
        if meta.get(key) is not None and not (isinstance(meta[key], str) and URL_RE.match(meta[key])):
            errors.append(f"{key} must be an http(s) URL")
    credits = meta.get("credits")
    if credits is not None:
        if not isinstance(credits, list) or any(not isinstance(c, dict) or not c.get("what") or not c.get("author") or not c.get("license") for c in credits):
            errors.append("credits: a list of {what, author, license, url?} for anything you didn't make yourself (fonts, textures, code)")
        elif any(c.get("url") is not None and not (isinstance(c["url"], str) and URL_RE.match(c["url"])) for c in credits):
            errors.append("credits[].url must be an http(s) URL")
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
        if k not in ("id", "name", "blurb", "author", "authorUrl", "license", "version", "tags", "homepage", "clockSafe", "credits"):
            warnings.append(f"saver.json: unknown key {k!r} is ignored")
    return meta, errors, warnings


def gallery_html(index: list[dict]) -> str:
    """The README gallery: preview, name, author (linked when authorUrl is given), license; three to a row."""
    cells = []
    for it in index:
        by = html.escape(it["author"])
        if it.get("authorUrl"):
            by = f'<a href="{html.escape(it["authorUrl"], quote=True)}">{by}</a>'
        cells.append(f'<td align="center" valign="top" width="33%"><a href="{it["path"]}"><img src="{it["preview"]}" alt="{html.escape(it["name"], quote=True)}" width="100%"></a>'
                     f'<br><b>{html.escape(it["name"])}</b><br><sub>by {by} · {html.escape(it["license"])}</sub></td>')
    rows = "\n".join("<tr>\n" + "\n".join(cells[i:i + 3]) + "\n</tr>" for i in range(0, len(cells), 3))
    return f"{START}\n<table>\n{rows}\n</table>\n{END}"


def readme_with_gallery(index: list[dict]) -> str | None:
    text = README.read_text()
    if START not in text or END not in text:
        return None
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    return head + gallery_html(index) + tail


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
            "authorUrl": meta.get("authorUrl", ""), "license": meta.get("license", ""), "version": meta.get("version", "1.0"),
            "tags": meta.get("tags", []), "credits": meta.get("credits", []), "clockSafe": meta.get("clockSafe", True),
            "path": f"screensavers/{folder.name}", "preview": f"screensavers/{folder.name}/{preview.name}", "files": files,
        })
    idx = json.dumps({"format": 1, "kind": "screensaver", "items": index}, indent=1, ensure_ascii=False) + "\n"
    readme = readme_with_gallery(index)
    stale = []
    if check_only:
        if not (ROOT / "index.json").exists() or (ROOT / "index.json").read_text() != idx:
            stale.append("index.json")
        if readme is not None and readme != README.read_text():
            stale.append("README.md (gallery)")
        for st in stale:
            print(f"  stale: {st} (run scripts/validate.py and commit)")
    else:
        (ROOT / "index.json").write_text(idx)
        if readme is not None:
            README.write_text(readme)
    print(f"{len(index)} screensaver{'s' if len(index) != 1 else ''} ok, {bad} with errors" + (f", {len(stale)} generated file(s) stale" if stale else ""))
    return 1 if bad or stale else 0


if __name__ == "__main__":
    sys.exit(main())
