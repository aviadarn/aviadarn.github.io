"""Add the kitchen-accident anticipation card to the bundled site export.

index.html is a self-unpacking bundle. Two of its <script> blocks carry data:
a manifest of gzip+base64 modules, and the page itself as a JSON string. Both
sit INSIDE script elements, so every "</" in them is escaped as "<\\u002F" --
a literal </script> would end the element early and the loader would read
truncated data. Re-serialising either block with json.dumps loses that and
breaks the page, so this splices in pre-escaped text and leaves the rest of
each line byte for byte as it was.
"""

import base64
import gzip
import json
import pathlib

ROOT = pathlib.Path("/Users/aviad/Documents/aviad-site")

CARD = """ { id:'kitchen', topic:'perception', year:2026, cost:'$1.93 GPU', title:'Can a video model see a kitchen accident coming?',
   short:"Nexar's BADAS model warns of car crashes seconds ahead. I applied the same recipe to kitchens: hand-labeled YouTube fail clips, then a small head on frozen V-JEPA2 video features. It beats a single frame, but part of what it learned is \\u201cthis looks like a YouTube fail video\\u201d.",
   num:'34 vs 1', numLabel:'false alarms per hour on calm YouTube footage vs. normal cooking, same threshold',
   caught:'The single-frame baseline looked better at catching accidents in time. It was firing through fail videos before anything went wrong: it had learned the YouTube look, not danger.',
   img:A+'kitchen-false-alarms.png', repo:'https://github.com/aviadarn/kitchen-sentinel',
   stats:[{v:'0.56 vs 0.47',l:'hard AP, video model vs. single frame'},{v:'0.52',l:'AUC of BADAS-Open as is: roads do not transfer'},{v:'95 of 666',l:'clips I labeled that show a kitchen accident'},{v:'0.43 s',l:'median warning before an accident'}],
   details:['Hard AP ranks each clip\\u2019s warning moments against its own earlier, calm moments, so source and camera are held fixed. 5-fold cross-validation, grouped by compilation.','BADAS-Open\\u2019s checkpoint also feeds its head 1 s of future tokens imagined by V-JEPA2\\u2019s predictor. I reproduced that for the zero-shot baseline and checked it against their code.','Adding 11 minutes of calm YouTube footage to training halved those false alarms, 34 to 19 an hour. It did not remove them.'],
   limits:'89 usable clips and one labeler, so intervals are wide. 34 of them start too late to show any calm footage before the warning.' },
"""

PROSE = [
    "Nexar's BADAS-Open predicts car crashes from dashcam video: a frozen V-JEPA2 ViT-L encoder, an attention head, a P(danger) for every 2 s window. I applied the recipe to kitchens — cuts, burns, fire, falling objects, slips. No public dataset of kitchen accidents with a warning period exists, so I built one. A SigLIP filter pulled 995 kitchen candidates out of the 29,940 clips in the Oops! fail-video dataset, and I labeled 666 of them in a keyboard tool written for it: keep or reject, hazard type, and two marks per accident — when danger first becomes visible, and when it happens. 95 survived. Normal cooking came from 14.7 hours of Charades and EPIC-KITCHENS.",
    "The labels set the difficulty. The median warning is 0.43 s, and 34 of the 89 clips with a full window before the accident start too late to show any calm footage first. This is closer to spotting a failure as it starts than to seeing it coming seconds ahead. There are too few clips for a fixed test split, so every number is out-of-fold from 5-fold cross-validation grouped by compilation, with the alarm threshold set per fold for at most one false alarm an hour on normal cooking.",
    {"table": [["Model", "hard AP", "caught on time", "false alarms/h, cooking", "false alarms/h, calm YouTube"],
               ["class prior", "0.23", "0%", "0", "0"],
               ["BADAS-Open, zero-shot", "0.24", "0%", "1.2", "11"],
               ["SigLIP, last frame", "0.47", "41%", "1.0", "100"],
               ["V-JEPA2 probe, 3 seeds", "0.56", "28%", "1.2", "34"]]},
    "BADAS-Open does not transfer: AUC 0.52 on kitchens. Its checkpoint turned out to feed its head 512 tokens that V-JEPA2's predictor imagines one second ahead, concatenated after the 2,048 it actually sees — a straight port of the head misses them. I reproduced that and checked it against their per-sample loop before trusting a zero.",
    "The probe beats a single frame on hard AP — warning windows ranked against the same clip's earlier calm ones, so source and camera are held fixed — by 0.09, with a 95% interval of +0.01 to +0.17. But at the alarm threshold the single frame caught more accidents in time, 41% against 28%. That is where the evaluation earned its keep.",
    "Every accident clip is a YouTube fail compilation and every normal clip is not. On calm stretches of fail clips, before anything has gone wrong, the single frame separates them from normal cooking with AUC 0.93 and fires on 7% of them. It had learned the YouTube look. The probe sits at 0.71 and fires on 1.8%; inside the labeled warnings it fires 15 times more often than before them, against 5 times for the single frame.",
    "So I added the control: 125 kitchen clips I had not kept, cut 1.5 s before their failure marker — 11 minutes of YouTube footage where nothing goes wrong. At the same threshold they draw 100 false alarms an hour from the single frame and 34 from the probe, against about one on cooking. Training on them halves that, to 56 and 19. It does not remove it; eleven minutes is too little to unlearn a style.",
    "The model is not the bottleneck. The next step is data: accident clips cut with five seconds of lead-in, and the roughly 3,300 Oops clips with four or more seconds before their failure as same-source normal footage. Fine-tuning comes after that, not before.",
]


def escaped(text: str) -> str:
    """JSON string body, with "</" hidden from the HTML parser."""
    return json.dumps(text, ensure_ascii=True)[1:-1].replace("</", "<\\u002F")


def render(entry) -> str:
    if isinstance(entry, dict):
        return "{table:" + json.dumps(entry["table"], ensure_ascii=False) + "}"
    return json.dumps(entry, ensure_ascii=False)


def main() -> None:
    path = ROOT / "index.html"
    lines = path.read_text().split("\n")

    page_index = next(i for i, line in enumerate(lines)
                      if line.startswith('"<!DOCTYPE html>'))
    anchor = escaped("{ id:'lidar',")
    assert anchor in lines[page_index], "anchor card not found"
    assert "id:'kitchen'" not in lines[page_index], "card already present"
    lines[page_index] = lines[page_index].replace(anchor, escaped(CARD.lstrip()) + escaped(" ") + anchor, 1)

    blob_index = next(i for i, line in enumerate(lines)
                      if line.startswith('{"') and '"mime"' in line)
    blob = json.loads(lines[blob_index])
    key = next(k for k, v in blob.items()
               if v.get("compressed") and "PORTFOLIO_ORIGINAL"
               in gzip.decompress(base64.b64decode(v["data"])).decode())
    before = blob[key]["data"]
    source = gzip.decompress(base64.b64decode(before)).decode()
    assert "kitchen: [" not in source, "prose already present"

    block = "kitchen: [\n" + ",\n".join(render(entry) for entry in PROSE) + "\n],\n"
    source = source.replace("window.PORTFOLIO_ORIGINAL = {\n",
                            "window.PORTFOLIO_ORIGINAL = {\n" + block, 1)
    after = base64.b64encode(gzip.compress(source.encode(), mtime=0)).decode()
    assert before in lines[blob_index]
    lines[blob_index] = lines[blob_index].replace(before, after, 1)

    path.write_text("\n".join(lines))
    print("card and prose inserted")


if __name__ == "__main__":
    main()
