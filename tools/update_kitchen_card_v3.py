"""Kitchen card, v3: three hours of calm YouTube footage in training removes the YouTube shortcut.

index.html is a self-unpacking bundle. The card list lives in a JSON string inside a <script> block
and the prose in a gzip+base64 module inside another, so every "</" in either is escaped as
"<\\u002F" -- a literal </script> would end the element early and the loader would read truncated
data. This swaps the kitchen card and its write-up as whole pre-escaped blocks and leaves everything
around them byte for byte.
"""

import base64
import gzip
import json
import pathlib

ROOT = pathlib.Path("/Users/aviad/Documents/aviad-site")

CARD = """{ id:'kitchen', topic:'perception', year:2026, cost:'$5.38 GPU', title:'Can a video model see a kitchen accident coming?',
   short:"Nexar's BADAS model warns of car crashes seconds ahead. I applied the same recipe to kitchens: hand-labeled YouTube fail clips, then a small head on frozen V-JEPA2 video features. At first part of what it learned was \\u201cthis looks like a YouTube fail video\\u201d; three hours of calm YouTube footage in training removed that.",
   num:'34 \\u2192 1.9', numLabel:'false alarms per hour on calm YouTube footage, before and after training on 3 hours of it',
   caught:'The single-frame baseline looked better at catching accidents in time. It was firing through fail videos before anything went wrong: it had learned the YouTube look, not danger.',
   img:A+'kitchen-false-alarms-v3.png', video:A+'kitchen-prediction-loop.mp4', repo:'https://github.com/aviadarn/kitchen-sentinel',
   stats:[{v:'26%',l:'accidents caught in time, at 1 false alarm an hour on cooking'},{v:'0.52',l:'AUC of BADAS-Open as is: roads do not transfer'},{v:'95 of 666',l:'clips I labeled that show a kitchen accident'},{v:'0.43 s',l:'median warning before an accident'}],
   details:['Hard AP ranks each clip\\u2019s warning moments against its own earlier, calm moments, so source and camera are held fixed. 5-fold cross-validation, grouped by compilation.','BADAS-Open\\u2019s checkpoint also feeds its head 1 s of future tokens imagined by V-JEPA2\\u2019s predictor. I reproduced that for the zero-shot baseline and checked it against their code.','2,092 Oops clips, kitchen or not, cut 3 s before their failure: three hours where nothing has gone wrong yet. Trained with them, the video model fires on 0.1% of calm YouTube moments, from 1.8%, and still catches 26% of accidents in time against 28%.'],
   limits:'89 usable clips and one labeler, so intervals are wide. 34 of them start too late to show any calm footage before the warning. Not yet tested on a fixed kitchen camera.' },
"""

PROSE = [
    "Nexar's BADAS-Open predicts car crashes from dashcam video: a frozen V-JEPA2 ViT-L encoder, an attention head, a P(danger) for every 2 s window. I applied the recipe to kitchens — cuts, burns, fire, falling objects, slips. No public dataset of kitchen accidents with a warning period exists, so I built one. A SigLIP filter pulled 995 kitchen candidates out of the 29,940 clips in the Oops! fail-video dataset, and I labeled 666 of them in a keyboard tool written for it: keep or reject, hazard type, and two marks per accident — when danger first becomes visible, and when it happens. 95 survived. Normal cooking came from 14.7 hours of Charades and EPIC-KITCHENS.",
    "The labels set the difficulty. The median warning is 0.43 s, and 34 of the 89 clips with a full window before the accident start too late to show any calm footage first. This is closer to spotting a failure as it starts than to seeing it coming seconds ahead. There are too few clips for a fixed test split, so every number is out-of-fold from 5-fold cross-validation grouped by compilation, with the alarm threshold set per fold for at most one false alarm an hour on normal cooking.",
    {"table": [["Model", "hard AP", "caught on time", "false alarms/h, cooking", "false alarms/h, calm YouTube"],
               ["class prior", "0.23", "0%", "0", "0"],
               ["BADAS-Open, zero-shot", "0.24", "0%", "1.2", "7"],
               ["SigLIP, last frame", "0.47", "41%", "1.0", "162"],
               ["V-JEPA2 probe, 3 seeds", "0.56", "28%", "1.2", "34"],
               ["V-JEPA2 probe + 3 h calm YouTube", "0.54", "26%", "1.2", "1.9"]]},
    "BADAS-Open does not transfer: AUC 0.52 on kitchens. Its checkpoint turned out to feed its head 512 tokens that V-JEPA2's predictor imagines one second ahead, concatenated after the 2,048 it actually sees — a straight port of the head misses them. I reproduced that and checked it against their per-sample loop before trusting a zero.",
    "The probe beats a single frame on hard AP — warning windows ranked against the same clip's earlier calm ones, so source and camera are held fixed — by 0.09, with a 95% interval of +0.01 to +0.17. But at the alarm threshold the single frame caught more accidents in time, 41% against 28%. That is where the evaluation earned its keep.",
    "Every accident clip is a YouTube fail compilation and every normal clip is not. On calm stretches of fail clips, before anything has gone wrong, the single frame separates them from normal cooking with AUC 0.93 and fires on 7% of them. It had learned the YouTube look. The probe sits at 0.71 and fires on 1.8%; inside the labeled warnings it fires 15 times more often than before them, against 5 times for the single frame.",
    "So I added the control at scale: every Oops clip I had not labeled as an accident, kitchen or not, cut three seconds before its failure marker — 2,092 clips, three hours of YouTube footage where nothing has gone wrong yet. Scored by models that never trained on them, they draw 162 false alarms an hour from the single frame and 34 from the probe, against about one on cooking. Training on them brings the probe to 1.9 an hour, while it catches accidents as before: 26% in time against 28%. The single frame drops to 8 but still separates kitchen fail clips from cooking with AUC 0.91; the probe falls to 0.66. An 11-minute version of the same fix had only halved the false alarms.",
    {"img": "kitchen-false-alarms-v3.png",
     "alt": "False alarms per hour on normal cooking and on calm YouTube footage: single frame 1.0 and 162.1, "
            "video probe 1.2 and 34.4, video probe trained on 3 hours of calm YouTube footage 1.2 and 1.9"},
    "I also tried generating more accidents: Wan 2.2 continued real cooking frames once into an accident and once into nothing. On review the clips looked generated — glasses breaking before they fall, fires without a cause — so none of them went into training.",
    "The remaining limit is the accident clips: 89 of them, with warnings under half a second, and a third with no calm footage before the warning. The next step is more of those, cut with five seconds of lead-in. Fine-tuning comes after that, not before.",
]


def escaped(text: str) -> str:
    """JSON string body, with "</" hidden from the HTML parser."""
    return json.dumps(text, ensure_ascii=True)[1:-1].replace("</", "<\\u002F")


def render(entry) -> str:
    if isinstance(entry, dict) and "table" in entry:
        return "{table:" + json.dumps(entry["table"], ensure_ascii=False) + "}"
    if isinstance(entry, dict):
        return "{img:" + json.dumps(entry["img"]) + ",alt:" + json.dumps(entry["alt"], ensure_ascii=False) + "}"
    return json.dumps(entry, ensure_ascii=False)


def main(card: str = CARD, prose: list = PROSE, version: str = "v3") -> None:
    path = ROOT / "index.html"
    lines = path.read_text().split("\n")

    page = next(i for i, line in enumerate(lines) if line.startswith('"<!DOCTYPE html>'))
    html = json.loads(lines[page])
    old_card = html[html.index("{ id:'kitchen'"):html.index("{ id:'lidar'")]
    new_card = card + " "  # the card list puts "\n " between cards
    before, after = escaped(old_card), escaped(new_card)
    if lines[page].count(before) != 1:
        raise SystemExit("kitchen card block not found exactly once")
    lines[page] = lines[page].replace(before, after, 1)

    blob_index = next(i for i, line in enumerate(lines) if line.startswith('{"') and '"mime"' in line)
    blob = json.loads(lines[blob_index])
    key = next(k for k, v in blob.items()
               if v.get("compressed") and "PORTFOLIO_ORIGINAL"
               in gzip.decompress(base64.b64decode(v["data"])).decode())
    data = blob[key]["data"]
    source = gzip.decompress(base64.b64decode(data)).decode()
    start = source.index("kitchen: [\n")
    end = source.index("\n],\n", start) + len("\n],\n")
    source = source[:start] + "kitchen: [\n" + ",\n".join(render(e) for e in prose) + "\n],\n" + source[end:]
    new_data = base64.b64encode(gzip.compress(source.encode(), mtime=0)).decode()
    assert data in lines[blob_index]
    lines[blob_index] = lines[blob_index].replace(data, new_data, 1)

    path.write_text("\n".join(lines))
    print(f"kitchen card and write-up at {version}")


if __name__ == "__main__":
    main()
