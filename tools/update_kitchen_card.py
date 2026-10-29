"""Kitchen card: a prediction loop on the card, and the false-alarm chart inside the write-up.

index.html is a self-unpacking bundle. The card list and the page template live in a JSON string
inside a <script> block and the prose in a gzip+base64 module inside another, so every "</" in
either is escaped as "<\\u002F" -- a literal </script> would end the element early and the loader
would read truncated data. Re-serialising a whole line with json.dumps loses that and breaks the
page, so this replaces pre-escaped fragments and leaves everything around them byte for byte.

Write-up blocks could be text or tables; this adds a third kind, {img: 'file in assets/', alt}.
"""

import base64
import gzip
import json
import pathlib

ROOT = pathlib.Path("/Users/aviad/Documents/aviad-site")


def escaped(text: str) -> str:
    """JSON string body, with "</" hidden from the HTML parser."""
    return json.dumps(text, ensure_ascii=True)[1:-1].replace("</", "<\\u002F")


PAGE_EDITS = [
    # (old, new), both unescaped. The card gets the loop; its chart stays as img, as on the carry card.
    ("img:A+'kitchen-false-alarms.png', repo:",
     "img:A+'kitchen-false-alarms.png', video:A+'kitchen-prediction-loop.mp4', repo:"),
    # Write-up blocks: strings are text, {table} a table, and now {img} an image from assets/.
    ("const full = (O[p.id] || []).map(b => typeof b === 'string' ? { isText: true, isTable: false, text: b } "
     ": { isText: false, isTable: true, rows:",
     "const full = (O[p.id] || []).map(b => typeof b === 'string' ? { isText: true, isTable: false, isImage: false, "
     "text: b } : b.img ? { isText: false, isTable: false, isImage: true, src: A + b.img, alt: b.alt || '' } "
     ": { isText: false, isTable: true, isImage: false, rows:"),
    ("</sc-raw-table>\n              </div>\n            </sc-if>\n          </sc-for>",
     "</sc-raw-table>\n              </div>\n            </sc-if>\n"
     "            <sc-if value=\"{{ b.isImage }}\" hint-placeholder-val=\"{{ false }}\">\n"
     "              <img class=\"washed\" src=\"{{ b.src }}\" alt=\"{{ b.alt }}\" loading=\"lazy\" "
     "style=\"width:100%;display:block;border-radius:var(--radius-md)\">\n"
     "            </sc-if>\n          </sc-for>"),
]

CHART = ('{img:"kitchen-false-alarms.png",alt:"False alarms per hour on normal cooking and on calm YouTube '
         'footage: single frame 1.0 and 100.5, video probe 1.2 and 33.5, video probe trained on 11 minutes of '
         'YouTube footage 1.8 and 18.6"}')
PROSE_ANCHOR = ',\n"The model is not the bottleneck.'


def main() -> None:
    path = ROOT / "index.html"
    lines = path.read_text().split("\n")

    page = next(i for i, line in enumerate(lines) if line.startswith('"<!DOCTYPE html>'))
    for old, new in PAGE_EDITS:
        before, after = escaped(old), escaped(new)
        found = lines[page].count(before)
        if found != 1:
            raise SystemExit(f"page fragment appears {found} times: {old[:60]!r}")
        lines[page] = lines[page].replace(before, after, 1)

    blob_index = next(i for i, line in enumerate(lines) if line.startswith('{"') and '"mime"' in line)
    blob = json.loads(lines[blob_index])
    key = next(k for k, v in blob.items()
               if v.get("compressed") and "PORTFOLIO_ORIGINAL"
               in gzip.decompress(base64.b64decode(v["data"])).decode())
    before = blob[key]["data"]
    source = gzip.decompress(base64.b64decode(before)).decode()
    if source.count(PROSE_ANCHOR) != 1 or 'img:"kitchen-false-alarms.png"' in source:
        raise SystemExit("kitchen prose anchor missing, repeated, or chart already present")
    source = source.replace(PROSE_ANCHOR, ",\n" + CHART + PROSE_ANCHOR, 1)
    after = base64.b64encode(gzip.compress(source.encode(), mtime=0)).decode()
    assert before in lines[blob_index]
    lines[blob_index] = lines[blob_index].replace(before, after, 1)

    path.write_text("\n".join(lines))
    print("loop on the card, chart in the write-up")


if __name__ == "__main__":
    main()
