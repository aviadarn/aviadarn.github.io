"""Bring the Pokemon card up to the four-milestone result.

index.html is a self-unpacking bundle. The card list lives in a JSON string
inside a <script> block and the prose in a gzip+base64 module inside another,
so every "</" in either is escaped as "<\\u002F" -- a literal </script> would
end the element early and the loader would read truncated data. Re-serialising
a whole line with json.dumps loses that and breaks the page, so this replaces
pre-escaped fragments and leaves everything around them byte for byte.
"""

import base64
import gzip
import json
import pathlib

ROOT = pathlib.Path("/Users/aviad/Documents/aviad-site")


def escaped(text: str) -> str:
    """JSON string body, with "</" hidden from the HTML parser."""
    return json.dumps(text, ensure_ascii=True)[1:-1].replace("</", "\\u003C/")


CARD_EDITS = [
    # (old fragment, new fragment) -- both pre-escaping.
    (
        "It walks the whole opening route of Pok\u00e9mon Yellow \u2014 bedroom, downstairs, across town, into Oak's lab.",
        "From the first frame of a new game it plays the whole opening of Pok\u00e9mon Yellow: out of the bedroom, across town, into Oak's lab, through the Pikachu hand-over and the rival's battle, and out of Pallet Town onto Route 1.",
    ),
    (
        "num:'2.42 \u2192 0.27', numLabel:'tiles of error in where the model thinks the player will be',",
        "num:'0/4 \u2192 4/4', numLabel:'story milestones, from a new game, on two of three seeds',",
    ),
    (
        "caught:'The model beat a no-change baseline by 44\u2013631\u00d7 at predicting, and was still worse than assuming the player never moved at saying where the player is.',",
        "caught:'Almost none of what was stopping it was navigation. A story beat fires on an exact tile, facing an exact direction, and A is not a safe button \u2014 it answered YES to \u201Cgive a nickname?\u201D and spent 207 presses trapped in a naming screen whose exit is a button the action set does not have.',",
    ),
    ("img:A+'pokeyellow-route.gif'", "img:A+'pokeyellow-milestones.gif'"),
    (
        "stats:[{v:'38/38',l:'route waypoints, bedroom to Oak\\u2019s lab'},{v:'3/3',l:'runs reaching the Pikachu encounter, from 0/3'},{v:'0.27',l:'tiles of error one step ahead, from 2.42'},{v:'0/4',l:'story milestones \u2014 the hand-over still fails'}],",
        "stats:[{v:'4/4',l:'milestones on two of three seeds, from 0/4'},{v:'442',l:'actions from a new game to Route 1'},{v:'0.27',l:'tiles of error one step ahead, from 2.42'},{v:'3/3',l:'seeds that get Pikachu and win the rival fight'}],",
    ),
    (
        "'Six further bugs sat between the isolated navigation result and playing the game, every one in the controller rather than the model.'",
        "'Six further bugs sat between the isolated navigation result and playing the game, every one in the controller rather than the model.','Then ten more between walking the route and finishing the story, and they were about what a Game Boy does with a button rather than about the model. The hand-over fires on tile (4, 7) facing up; the route\\u2019s last waypoint is where the scene CARRIES the player, and standing there under your own power does nothing \u2014 489 A presses at a table that was not there.','Four-adjacency invents floor: two tiles side by side in the data with a counter between them, one of them only recorded because a cutscene put the player on it. Walls are learned by walking into them now.'"
    ),
    (
        "limits:'It does not finish the first milestone: the route ends standing in front of Oak, and receiving Pikachu is a scripted exchange that 489 A presses do not complete. Yellow only, one ROM, one route.'",
        "limits:'One seed of three still misses the last milestone: it walks back into the lab, where the cost field is flat because no episode in the data ever walked out. Past Pallet the run is on ground nothing ever recorded, so neither the cost field nor the position read-out means anything out there \u2014 the next thing is data, not a better planner. Yellow only, one ROM, one route.'",
    ),
]

PROSE_APPEND = [
    "Then the milestone chain, which turned out not to be a navigation problem at all. The planner had been walking the route for some time; what it could not do was press the right button on the right square. Pikachu's hand-over fires on tile (4, 7) in Oak's lab, facing up \u2014 the ball is on the table north of it. The route's last recorded waypoint is (3, 5), which is where the scene CARRIES the player afterwards, so the run walked there under its own power, reported every waypoint complete, and pressed A for 489 actions at a table that was not there. Reached facing east, sixty A presses do nothing; one `up` first and the party holds a Pikachu thirty-four presses later.",
    "A is not a safe button. The scene ends on \u201Cdo you want to give a nickname?\u201D, where A answers YES and opens a naming screen in which A types another letter, B deletes one, and the way out is a button this six-action set does not have: 207 A presses at one tile, unable to move. B is no answer either, because in Gen 1 it does not advance text at all \u2014 twenty-four B presses left Oak mid-sentence. `down` then A turns the page and declines the question, and the rival's fight starts twenty-three actions later.",
    "Four-adjacency invents floor. (4, 4) and (4, 5) are both in the recorded positions and a counter runs between them; (4, 5) is only in the data because a cutscene put the player there. The field read one hop to the trigger tile and the planner pressed right into the counter thirty-three times. Walls are learned by walking into them now, and the edge is dropped from the BFS.",
    "A tile can also appear twice. Map 0 (0, 10) is both where Oak stops the player on the way out of Pallet and where leaving Pallet for good happens, and his scene steps onto it, walks them south and steps onto it again \u2014 which marked the exit done before the player had a Pokemon. And whether a tile can be stood on at all depends on the side it is approached from: one press walks one tile or two depending on what is beyond it, so (4, 7) is reachable only from below.",
    {"table": [["milestone", "seed 0", "seed 1", "seed 2"],
               ["Pikachu", "yes", "yes", "yes"],
               ["rival's battle", "yes", "yes", "yes"],
               ["out of the lab", "yes", "yes", "yes"],
               ["out of Pallet", "no", "yes", "yes"]]},
    "What stops the last one on seed 0 is the data, not the search: the run steps out of the lab and back in, and from inside the lab no tile in Pallet has any cost at all, because no episode in the dataset ever walked out of that door. Reversing recorded doorways fixes that and costs more than it buys \u2014 it hands the planner a door as a shortcut between rooms it never walked that way, and two of three seeds went from four milestones to none. It is a flag, off by default, with that measurement beside it.",
]


def render(entry) -> str:
    if isinstance(entry, dict):
        return "{table:" + json.dumps(entry["table"], ensure_ascii=False) + "}"
    return json.dumps(entry, ensure_ascii=False)


def main() -> None:
    path = ROOT / "index.html"
    lines = path.read_text().split("\n")

    page = next(i for i, line in enumerate(lines)
                if line.startswith('"<!DOCTYPE html>'))
    for old, new in CARD_EDITS:
        before, after = escaped(old), escaped(new)
        found = lines[page].count(before)
        if found != 1:
            raise SystemExit(f"card fragment appears {found} times: {old[:60]!r}")
        lines[page] = lines[page].replace(before, after, 1)

    blob_index = next(i for i, line in enumerate(lines)
                      if line.startswith('{"') and '"mime"' in line)
    blob = json.loads(lines[blob_index])
    key = next(k for k, v in blob.items()
               if v.get("compressed") and "PORTFOLIO_ORIGINAL"
               in gzip.decompress(base64.b64decode(v["data"])).decode())
    before = blob[key]["data"]
    source = gzip.decompress(base64.b64decode(before)).decode()
    # The last paragraph of the block is the one the result overturns, so it
    # is replaced rather than appended to.
    anchor = '"What it does not do is finish the first milestone.'
    start = source.index(anchor)
    end = source.index("\n", start)
    source = (source[:start]
              + ",\n".join(render(entry) for entry in PROSE_APPEND)
              + source[end:])
    after = base64.b64encode(gzip.compress(source.encode(), mtime=0)).decode()
    lines[blob_index] = lines[blob_index].replace(before, after, 1)

    path.write_text("\n".join(lines))
    print("card and prose updated")


if __name__ == "__main__":
    main()
