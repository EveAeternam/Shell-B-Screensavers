# Contributing a screensaver

1. Fork the repository and add a folder `screensavers/<id>/` (lowercase letters, digits and dashes; the id must be new)
   with `saver.json`, `index.html` and `preview.jpg`. Put images, fonts and extra scripts under `assets/` and reference
   them with relative paths.
2. Fill in `name`, `blurb`, `author` and `license` (an SPDX id: MIT, CC0-1.0, CC-BY-4.0). By opening a pull request you
   agree that the screensaver is shared under the license you named. `author` is how you want to be credited (it shows
   in Shell:B and in the README gallery); add `authorUrl` to link it. Anything you didn't make yourself (a font, a
   texture, borrowed code) goes in `credits` with its own license, which must allow redistribution.
3. Run `python3 -I scripts/validate.py` from the repository root and fix every error. Warnings point at the rules in
   the README (reduced motion, resize) that the script can only guess at; read them.
4. Make the preview with `scripts/preview.sh screensavers/<id>` (headless Firefox), or take a screenshot of the first
   seconds yourself and save it as a JPEG around 640×360, under 400 KB.
5. Let it run for an hour in a browser tab and watch the memory in the task manager: it must not grow.
6. Commit the folder, `index.json` and `README.md` (the script rewrites its gallery), and open a pull request; the
   template has the checklist. Without git, open a *Submit a screensaver* issue with a link to the files and a
   maintainer adds it with you as the author.

Reviews look at the rules in the README and at the piece itself: it should be beautiful at 3 a.m. with nobody watching.
Screensavers that imitate a company's branding, show text or images that aren't yours, or load anything from the
network are not merged.

Updating a screensaver: bump `version`, keep the id.
