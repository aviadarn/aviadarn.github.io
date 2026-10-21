"""Add the Pokemon world-model card to the bundled site export.

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

CARD = """ { id:'poke', topic:'perception', year:2026, cost:'$0, on a MacBook', title:'A world model that learns to play Pokémon',
   short:"A model watches Game Boy pixels and learns to predict what happens next, with no rewards and no labels. A planner then searches that model for buttons to press. It walks the whole opening route of Pokémon Yellow — bedroom, downstairs, across town, into Oak's lab.",
   num:'2.42 → 0.27', numLabel:'tiles of error in where the model thinks the player will be',
   caught:'The model beat a no-change baseline by 44–631× at predicting, and was still worse than assuming the player never moved at saying where the player is.',
   img:A+'pokeyellow-route.gif', repo:'https://github.com/aviadarn/lepokeyellow',
   stats:[{v:'38/38',l:'route waypoints, bedroom to Oak\\u2019s lab'},{v:'3/3',l:'runs reaching the Pikachu encounter, from 0/3'},{v:'0.27',l:'tiles of error one step ahead, from 2.42'},{v:'0/4',l:'story milestones — the hand-over still fails'}],
   details:['Predicting embeddings well is not the same as predicting the game. Adding one term — read the player\\u2019s tile out of the PREDICTED embedding, not just the real frame — is what made planning work.','Fitting the read-out on predicted embeddings instead cut its error from 2.42 to 0.78 tiles and made the planner strictly worse: genuinely helpful moves went from 47.5% to 0%. Accuracy and usefulness pointed opposite ways.','Six further bugs sat between the isolated navigation result and playing the game, every one in the controller rather than the model.'],
   limits:'It does not finish the first milestone: the route ends standing in front of Oak, and receiving Pikachu is a scripted exchange that 489 A presses do not complete. Yellow only, one ROM, one route.' },
"""

PROSE = [
    "A JEPA world model trained on raw Game Boy pixels — a 12.5M-parameter encoder, a button-conditioned predictor, no rewards and no labels — and a planner that searches it for button presses. Ported from stmonty/lePokeRed to Pokémon Yellow, which is not a re-skin: Yellow moved one WRAM byte, so every address shifts by one, and it is a dual-mode cartridge that boots in colour unless you force DMG, which would have fed the model an arbitrary channel instead of luminance.",
    "The planner could not cross one open map, and four plausible causes were wrong. Not the horizon (14 against 30, identical). Not the action repeats (1, 2 and 4, identical). Not walls — that objection was real, the tile due north of the start is the doorway back into the player's own house, and a BFS cost field built from 31,759 recorded positions fixed it and changed nothing.",
    "Not the read-out's resolution either, which is what I concluded first. A linear probe placed the player to within 1.44–1.88 tiles while adjacent cost levels differ by one hop, so the signal genuinely sat under the noise floor of the instrument reading it. A two-layer head cut that to 0.53 and 0.48 tiles, with shuffled labels at −0.02 as the control — and navigation did not improve at all.",
    "Because the planner never reads a real screen. It decodes the predictor's output, and that is a different distribution. Held out, in tiles:",
    {"table": [["what is decoded", "before", "after"],
               ["the real frame", "0.22", "0.03"],
               ["assume the player never moved", "0.69", "0.52"],
               ["one-step rollout", "2.42", "0.27"]]},
    "The predictor was three and a half times worse than standing still at saying where the player will be, while its embedding MSE beat a no-change baseline by 44× to 631×. Those are not the same quantity and only one of them is what a planner uses. Nothing in the objective ever asked a predicted embedding to keep the player's tile legible, so it did not. Seeding the rollout with three real frames the way training does changes nothing, so it is not a train/test mismatch either.",
    "The obvious response makes it worse. Fitting the read-out on predicted embeddings cut one-step error from 2.42 to 0.78 tiles, and the decisions got worse: the share where the lowest predicted cost belongs to an action that genuinely helps went from 47.5% to 0%. Calibrating on blurred predictions teaches the conditional mean of position, which is exactly the part that discards the differences between actions — and ranking is the only thing a planner uses.",
    "So the fix is in the objective. A coordinate head reads (y, x) from an embedding and is trained against the tile the emulator recorded, on the predictor's output as well as the encoder's. On the isolated navigation task that is 0/3 to 3/3 runs reaching the Pikachu encounter, and the prediction loss improved as well.",
    "Then six separate bugs stood between that and actually playing, every one in the controller rather than the model: the cost field was never wired into the player; nothing stopped it repeating an action that did nothing, so it pressed down into a wall ten times; the dialogue rule fired on \"the tile stopped moving\" and then stopped planning until the tile moved, so it pressed A 116 of 162 actions at a signpost that opens and closes a text box; strides inside Oak's lab reach seven tiles, so four-adjacency left the lab in islands and only twelve tiles in the game could reach the waypoint inside it; being nearest to the last node counted as reaching it, which ended the run the instant the player stepped through the lab door; and looking two nodes ahead skipped the tile that starts Oak's encounter, so the planner walked into a lab with no Oak in it and pressed A in an empty room.",
    "A revisit penalty was needed, because two tiles each looked better from the other and the planner walked between them forty-four times. My first scale for it — 0.75 of a hop per visit, against a gradient of one hop per tile — inverted the cost field and sent the planner into unmapped ground. Small per visit with a high cap is the right shape: ordinary travel stays nearly free and a loop accumulates until it breaks itself.",
    "What it does not do is finish the first milestone. The route ends standing in front of Oak, and receiving Pikachu is a scripted exchange that 489 A presses do not complete, with or without turning to face him first. Navigation is the result here; the milestone is not.",
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
    anchor = escaped(" { id:'wm',")
    assert anchor in lines[page_index], "anchor card not found"
    assert "id:'poke'" not in lines[page_index], "card already present"
    lines[page_index] = lines[page_index].replace(anchor, escaped(CARD) + anchor, 1)

    blob_index = next(i for i, line in enumerate(lines)
                      if line.startswith('{"') and '"mime"' in line)
    blob = json.loads(lines[blob_index])
    key = next(k for k, v in blob.items()
               if v.get("compressed") and "PORTFOLIO_ORIGINAL"
               in gzip.decompress(base64.b64decode(v["data"])).decode())
    before = blob[key]["data"]
    source = gzip.decompress(base64.b64decode(before)).decode()
    assert "poke: [" not in source, "prose already present"

    block = "poke: [\n" + ",\n".join(render(entry) for entry in PROSE) + "\n],\n"
    source = source.replace("window.PORTFOLIO_ORIGINAL = {\n",
                            "window.PORTFOLIO_ORIGINAL = {\n" + block, 1)
    after = base64.b64encode(gzip.compress(source.encode(), mtime=0)).decode()
    assert before in lines[blob_index]
    lines[blob_index] = lines[blob_index].replace(before, after, 1)

    path.write_text("\n".join(lines))
    print("card and prose inserted")


if __name__ == "__main__":
    main()
