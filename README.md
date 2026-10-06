# aviadarn.github.io

Personal site — selected ML work, with the measurements.

`index.html` is a self-unpacking page exported from a design tool (React and fonts are
embedded in the file). Media lives in `assets/`. Served by GitHub Pages from the `main`
branch root; no build step.

To publish a new export:

    python3 tools/patch_bundle.py ~/Downloads/index.html

That copies the export to `index.html` and adds what the export leaves out: a real title
and description (link previews read the static HTML), favicon, Open Graph tags, and a
name-and-links fallback for visitors without JavaScript.
