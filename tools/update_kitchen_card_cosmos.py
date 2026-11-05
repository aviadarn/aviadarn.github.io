"""Kitchen card, v3 + Cosmos: NVIDIA's Cosmos3-Nano added as a zero-shot baseline.

Builds on the v3 card and write-up (tools/update_kitchen_card_v3.py, which explains the bundle
escaping): one more detail, one more table row, a paragraph after the false-alarm chart, and the
GPU total with the Cosmos run ($2.83) and the gallery fetch ($0.11).
"""

import update_kitchen_card_v3 as v3


def replaced(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one {old!r}")
    return text.replace(old, new)


COSMOS_DETAIL = ("NVIDIA\\u2019s Cosmos3-Nano, a general video-reasoning model, asked one yes/no question per window: "
                 "hard AP 0.42, between BADAS-Open and a single frame, and 37 false alarms an hour on calm YouTube "
                 "footage. It too partly reads the fail-video look.")

CARD = replaced(v3.CARD, "cost:'$5.38 GPU'", "cost:'$8.32 GPU'")
CARD = replaced(CARD, "against 28%.'],", f"against 28%.','{COSMOS_DETAIL}'],")

COSMOS = ("One more baseline came later: a general video-reasoning model, asked directly. NVIDIA's Cosmos3-Nano "
          "sees each window as 8 frames at 4 fps and is asked whether an accident is about to happen or starting; "
          "the score is P(yes) against P(no) for its first answer token, nothing tuned. It does better than "
          "BADAS-Open — hard AP 0.42 — but stays below a single frame and catches 11% of accidents in time. It is "
          "quiet on cooking, yet raises 37 false alarms an hour on the calm YouTube footage, and separates calm "
          "fail-clip moments from cooking with AUC 0.78: it too partly answers “is this a fail video”.")

PROSE = list(v3.PROSE)
table = list(PROSE[2]["table"])
table.insert(table.index(["BADAS-Open, zero-shot", "0.24", "0%", "1.2", "7"]) + 1,
             ["Cosmos3-Nano, zero-shot yes/no", "0.42", "11%", "1.4", "37"])
PROSE[2] = {"table": table}
PROSE.insert(next(i for i, e in enumerate(PROSE) if isinstance(e, dict) and "img" in e) + 1, COSMOS)

if __name__ == "__main__":
    v3.main(CARD, PROSE, "v3 + Cosmos")
