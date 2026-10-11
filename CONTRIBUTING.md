# Contributing a screensaver

1. Fork the repository and add a folder `screensavers/<id>/` (lowercase letters, digits and dashes; the id must be new)
   with `saver.json`, `index.html` and `preview.jpg`. Put images, fonts and extra scripts under `assets/` and reference
   them with relative paths.
2. Fill in `name`, `blurb`, `author` and `license` (an SPDX id: MIT, CC0-1.0, CC-BY-4.0). By opening a pull request you
   agree that the screensaver is shared under the license you named. Anything you didn't make yourself (a font, a
   texture) goes in `credits` in `saver.json` with its own license, and it must allow redistribution.
3. Run `python3 -I scripts/validate.py` from the repository root and fix every error. Warnings point at the rules in
   the README (reduced motion, resize) that the script can only guess at; read them.
4. Make the preview with `scripts/preview.sh screensavers/<id>` (headless Firefox), or take a screenshot of the first
   seconds yourself and save it as a JPEG around 640×360, under 400 KB.
5. Let it run for an hour in a browser tab and watch the memory in the task manager: it must not grow.
6. Commit the folder and the updated `index.json`, and open a pull request describing the piece.

Reviews look at the rules in the README and at the piece itself: it should be beautiful at 3 a.m. with nobody watching.
Screensavers that imitate a company's branding, show text or images that aren't yours, or load anything from the
network are not merged.

Updating a screensaver: bump `version`, keep the id.
