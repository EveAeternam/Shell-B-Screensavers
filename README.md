# Shell:B Screensavers

[![Validate](https://github.com/EveAeternam/Shell-B-Screensavers/actions/workflows/validate.yml/badge.svg)](https://github.com/EveAeternam/Shell-B-Screensavers/actions/workflows/validate.yml) [![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Community screensavers for [Shell:B](https://github.com/EveAeternam/Shell-B), the local-first AI workspace.
Part of the family with [Shell-B-Themes](https://github.com/EveAeternam/Shell-B-Themes) and [Shell-B-Agents](https://github.com/EveAeternam/Shell-B-Agents).

A Shell:B screensaver is one `index.html` (plus whatever it needs in its folder) that animates forever with nobody
touching it. Shell:B shows it full screen in a sandboxed frame when the computer has been idle for a while, and any key
or mouse movement dismisses it. Screensavers run with scripts only: no same-origin access, no network, no audio.

## Install one

In Shell:B open **Settings → Appearance → Screensaver style** and press **Browse community**. Each screensaver here
appears with its preview; **Install** makes it a Screensaver project in your Studio (where you can open the code and
change it) and selects it as your screensaver. Shell:B fetches this repository as a tarball at a pinned commit, so the
list works offline once fetched.

## Catalogue

| Screensaver | What it is |
|---|---|
| Synthwave Horizon | A striped sun over a neon grid scrolling toward you. Shell:B's original. |
| Starfield Warp | Nine hundred stars streaking past while the vanishing point drifts. |
| Bouncing Logo | The Shell:B tile bouncing off the walls, new colour on every hit, a flash on a corner. |
| Koi Pond | A pond at night from above: koi in schools, ripples, lily pads, moonlight. |
| Ink Currents | Ink particles riding a slowly turning flow field; the current and hue shift over minutes. |
| Harmonograph | Damped pendulums drawing Lissajous roses, one figure fading into the next. |

`index.json` is the machine-readable catalogue; each folder has a `preview.jpg`.

## Make one

Start from [`template/index.html`](template/index.html): a full-window canvas, a clamped-`dt` loop, resize handling, a
reduced-motion slowdown and a pause while hidden. Replace `draw()`. Or let Shell:B build it: in Shell:B, **Settings →
Appearance → Make one in the Studio**, describe what you'd like, and export the project when you're happy with it.

Every screensaver is a folder under `screensavers/`:

```
screensavers/koi-pond/
  saver.json      name, blurb, author, license, version, tags, clockSafe
  index.html      the piece; relative paths only
  preview.jpg     a frame from the first seconds, about 640×360 (≤ 400 KB)
  assets/         optional: images, fonts, extra scripts
```

`saver.json`:

```json
{
  "name": "Koi Pond",
  "blurb": "One or two sentences for the picker (≤ 200 characters).",
  "author": "Your name",
  "license": "MIT",
  "version": "1.0",
  "tags": ["water", "calm"],
  "clockSafe": true
}
```

`clockSafe` says the lower-left corner (about 30 % wide, 25 % tall) stays calm, because Shell:B may draw its clock
there. Set it to `false` if your piece uses the whole screen; the clock still shows, it just competes.

### The rules

They are the same ones Shell:B gives its own agents when they build a screensaver:

- It fills any aspect ratio: handle `resize`, no letterboxing, from 4:3 to ultrawide and portrait.
- Canvas 2D, SVG or CSS. Prefer Canvas 2D; there is no WebGL in the browser that takes the previews.
- A `requestAnimationFrame` loop with `dt` clamped, `devicePixelRatio` capped at 2, and no growth in memory or object
  count over hours: reuse particle pools, never append DOM nodes in the loop. Pause while `document.hidden`.
- Calm on the GPU. It must look good dark, since it often runs at night.
- Nothing static and bright, because it may run for hours on an OLED: drift every element slowly. Vary over minutes
  (seasons, palette shifts, new formations) so it never feels looped.
- No audio, no network, no external URLs: bundle every file in the folder. No controls, chrome, hover states or cursor.
- Respect `prefers-reduced-motion` by slowing to a gentle drift, not stopping.
- The first frame must already be a strong composition: previews capture the first second. Pre-roll a few frames if
  the piece needs to settle.
- Keep tuning constants (speeds, counts, palette) together at the top of the script.

Then check it and make the preview:

```bash
python3 -I scripts/validate.py          # rules above, sizes, index.json
scripts/preview.sh screensavers/<id>     # headless Firefox screenshot → preview.jpg
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the pull request checklist.

## License

The scripts and this repository are MIT. Each screensaver names its own license in `saver.json`; the ones here are MIT.

## Other collections

Shell:B installs from the whole family: [Shell-B-Themes](https://github.com/EveAeternam/Shell-B-Themes) and [Shell-B-Agents](https://github.com/EveAeternam/Shell-B-Agents) work the same way, with a validator, CI and a one-screen checklist each. Found a bug in the app itself? That goes to [Shell-B issues](https://github.com/EveAeternam/Shell-B/issues); questions and show-and-tell to [Discussions](https://github.com/EveAeternam/Shell-B/discussions).
