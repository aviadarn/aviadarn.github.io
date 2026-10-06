"""Install a design-tool export (self-unpacking "Bundled Page") as the site's index.html.

    python3 tools/patch_bundle.py ~/Downloads/index.html

The export's wrapper is titled "Bundled Page" with no description, which is what link
previews and search results read, and visitors without JavaScript see only "This page
requires JavaScript". This adds a real title, description, favicon, Open Graph tags and
lang, the same title inside the unpacked page, and a static name-and-links fallback.
The design itself is not touched. Fails loudly if the export's structure changes.
"""

import json
import re
import sys
from pathlib import Path

TITLE = "Aviad Aranias — ML engineer"
DESC = ("ML engineer — world models, robot policies, real-time video ML and GPU infrastructure. "
        "Measured results, reproducible code.")
FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' "
           "height='100' rx='18' fill='%2317365d'/><text y='70' x='50' text-anchor='middle' "
           "font-family='Helvetica,Arial' font-size='58' font-weight='bold' fill='white'>A</text></svg>")
FALLBACK = '''
    <div style="max-width:640px;margin:40px auto;padding:0 16px;font:16px/1.6 -apple-system,BlinkMacSystemFont,sans-serif;color:#222;">
      <h1 style="font-size:28px;margin-bottom:8px;">Aviad Aranias</h1>
      <p>ML engineer, Brooklyn NY. Robots, world models and real-time vision.</p>
      <p><a href="mailto:aviadarn@gmail.com">aviadarn@gmail.com</a> &middot;
         <a href="https://aviadarn.github.io/assets/Aviad-Aranias-CV.pdf">CV (PDF)</a> &middot;
         <a href="https://github.com/aviadarn">GitHub</a> &middot;
         <a href="https://www.linkedin.com/in/aviad-a-b0606682">LinkedIn</a></p>
    </div>'''


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
  <link rel="icon" href="{FAVICON}">'''
    s = replace_once(s, '<meta charset="utf-8">\n  <title>Bundled Page</title>', head, "wrapper title")
    s = replace_once(s, "<html>\n", '<html lang="en">\n', "<html> tag")
    ns = "      This page requires JavaScript to display.\n    </div>"
    s = replace_once(s, ns, ns + FALLBACK, "noscript message")
    # the template is a JSON string inside a <script>: escape accordingly
    meta = '<meta charset=\\"utf-8\\">\\n<meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1\\">'
    inner = ('\\n<title>' + TITLE.replace("—", "\\u2014") + '<\\u002Ftitle>\\n<meta name=\\"description\\" content=\\"'
             + DESC.replace("—", "\\u2014") + '\\">')
    s = replace_once(s, meta, meta + inner, "template head")
    tpl = json.loads(re.search(r'<script type="__bundler/template">(.*?)</script>', s, re.S).group(1))
    assert f"<title>{TITLE}</title>" in tpl
    out = Path(__file__).resolve().parents[1] / "index.html"
    out.write_text(s)
    print(f"wrote {out} ({len(s):,} bytes)")


if __name__ == "__main__":
    main(sys.argv[1])
