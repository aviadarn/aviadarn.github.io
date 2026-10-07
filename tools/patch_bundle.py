"""Install a design-tool export (self-unpacking "Bundled Page") as the site's index.html.

    python3 tools/patch_bundle.py ~/Downloads/index.html

The export's wrapper is titled "Bundled Page" with no description, which is what link
previews and search results read, and visitors without JavaScript see only "This page
requires JavaScript". This adds a real title, description, favicon, Open Graph tags and
lang, the same title and icons inside the unpacked page, and a static name-and-links fallback.

It also adds mobile fixes found by testing on iPhone (WebKit) and Pixel (Chromium) sizes
(MOBILE_CSS and VIDEO_JS below). Fails loudly if the export's structure changes.
"""

import json
import re
import sys
from pathlib import Path

TITLE = "Aviad Aranias — ML engineer"
DESC = ("ML engineer — world models, robot policies, real-time video ML and GPU infrastructure. "
        "Measured results, reproducible code.")
# robot icon: assets/favicon.svg, with PNG fallbacks and /favicon.ico for old browsers
ICONS = ('<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">\n'
         '  <link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">\n'
         '  <link rel="apple-touch-icon" href="assets/apple-touch-icon.png">')
FALLBACK = '''
    <div style="max-width:640px;margin:40px auto;padding:0 16px;font:16px/1.6 -apple-system,BlinkMacSystemFont,sans-serif;color:#222;">
      <h1 style="font-size:28px;margin-bottom:8px;">Aviad Aranias</h1>
      <p>ML engineer, Brooklyn NY. Robots, world models and real-time vision.</p>
      <p><a href="mailto:aviadarn@gmail.com">aviadarn@gmail.com</a> &middot;
         <a href="https://aviadarn.github.io/assets/Aviad-Aranias-CV.pdf">CV (PDF)</a> &middot;
         <a href="https://github.com/aviadarn">GitHub</a> &middot;
         <a href="https://www.linkedin.com/in/aviad-a-b0606682">LinkedIn</a></p>
    </div>'''


# Mobile fixes, all scoped by media query or attribute selector so desktop is unchanged:
#  - hero: the text column sat beside 160 px of decorative circles, leaving ~134 px for the
#    headline on a phone (one word per line); stack them, circles shrunk to an accent
#  - nav: on 320 px screens "Light mode" wrapped to two lines; the toggle becomes an icon
#  - upstream cards: minmax(300px) plus 28 px page padding overflowed a 320 px screen (match
#    without the comma: the browser serialises inline styles as "minmax(300px, 1fr)")
#  - touch screens: 44 px buttons (Apple's minimum tap target; the design uses 36 px)
#  - an open card: hide the sticky nav, which showed through the 72%-opaque backdrop
MOBILE_CSS = """
@media (max-width: 700px) {
  header[style*="grid-template-columns"] { grid-template-columns: 1fr !important; gap: 0 !important; }
  header[style*="grid-template-columns"] > [aria-hidden="true"] {
    order: -1; justify-self: end; width: 92px !important; margin: 0 0 -36px 0; }
}
@media (max-width: 400px) {
  header[style*="grid-template-columns"] > [aria-hidden="true"] { width: 72px !important; margin-bottom: 4px; }
}
@media (max-width: 420px) {
  nav[style*="sticky"] { padding-left: 16px !important; }
  nav[style*="sticky"] > span:first-child { font-size: 16px !important; }
  nav[style*="sticky"] .btn { padding-left: 12px; padding-right: 12px; white-space: nowrap; }
  nav[style*="sticky"] button[aria-label^="Switch"] { font-size: 0; width: 44px; padding: 0; }
  nav[style*="sticky"] button[aria-label^="Switch"]::before { content: "\\25D0"; font-size: 18px; line-height: 1; }
}
[style*="minmax(300px"] { grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)) !important; }
@media (pointer: coarse), (hover: none) { .btn { min-height: 44px; } }
body:has([role="dialog"]) nav[style*="sticky"] { visibility: hidden; }
"""

# The template marks every <video> autoplay muted loop playsinline, but the runtime drops the
# muted and loop attributes when it renders (the React `muted` quirk). Phones only autoplay
# muted video, so on Android the loops sat paused. Re-apply them to every video it inserts.
VIDEO_JS = """(function () {
  function fix(v) {
    if (v.__fixed) return; v.__fixed = true;
    v.muted = true; v.defaultMuted = true; v.setAttribute("muted", "");
    v.loop = true; v.playsInline = true; v.setAttribute("playsinline", "");
    var p = v.play && v.play(); if (p && p.catch) p.catch(function () {});
  }
  function scan() { document.querySelectorAll("video").forEach(fix); }
  new MutationObserver(scan).observe(document.documentElement, {childList: true, subtree: true});
  document.addEventListener("DOMContentLoaded", scan); scan();
})();"""


def replace_once(s: str, old: str, new: str, what: str) -> str:
    n = s.count(old)
    if n != 1:
        sys.exit(f"patch_bundle: expected one {what}, found {n}; the export format changed")
    return s.replace(old, new)


def main(src_path: str) -> None:
    s = Path(src_path).expanduser().read_text()
    head = f'''<meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{TITLE}</title>
  <meta name="description" content="{DESC}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://aviadarn.github.io/">
  <meta property="og:title" content="{TITLE}">
  <meta property="og:description" content="{DESC}">
  {ICONS}'''
    s = replace_once(s, '<meta charset="utf-8">\n  <title>Bundled Page</title>', head, "wrapper title")
    s = replace_once(s, "<html>\n", '<html lang="en">\n', "<html> tag")
    ns = "      This page requires JavaScript to display.\n    </div>"
    s = replace_once(s, ns, ns + FALLBACK, "noscript message")
    # the unpacked page: decode the JSON template, edit the HTML, re-encode. "</" is escaped
    # so nothing inside the string can close the <script> element that holds it.
    m = re.search(r'(<script type="__bundler/template">)(.*?)(</script>)', s, re.S)
    if not m:
        sys.exit("patch_bundle: no template block; the export format changed")
    tpl = json.loads(m.group(2))
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1">'
    extra = (f'\n<title>{TITLE}</title>\n<meta name="description" content="{DESC}">\n'
             + ICONS.replace("\n  ", "\n")
             + f'\n<style id="mobile-fixes">{MOBILE_CSS}</style>\n<script>{VIDEO_JS}</script>')
    tpl = replace_once(tpl, viewport, viewport + extra, "template viewport meta")
    enc = json.dumps(tpl).replace("</", "<\\u002F")
    s = s[:m.start(2)] + "\n" + enc + "\n  " + s[m.end(2):]
    tpl2 = json.loads(re.search(r'<script type="__bundler/template">(.*?)</script>', s, re.S).group(1))
    assert f"<title>{TITLE}</title>" in tpl2 and 'id="mobile-fixes"' in tpl2 and "__fixed" in tpl2
    out = Path(__file__).resolve().parents[1] / "index.html"
    out.write_text(s)
    print(f"wrote {out} ({len(s):,} bytes)")


if __name__ == "__main__":
    main(sys.argv[1])
