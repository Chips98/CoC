from __future__ import annotations


_DIALOGUE_SCENE_RULES = [
    ("boundary_setting", ["not welcome", "leave by", "leave tomorrow", "final decision", "not up for discussion"]),
    ("conflict", ["angry", "fight", "resent", "revenge", "hate", "attack"]),
    ("negotiation", ["deal", "price", "terms", "exchange", "offer", "contract", "buyer", "seller"]),
    ("competition", ["win", "beat", "rival", "undermine", "injure", "outperform"]),
    ("persuasion", ["persuade", "convince", "support", "commitment"]),
    ("repair", ["sorry", "apology", "repair", "make it right", "reconcile"]),
    ("trust_building", ["trust", "relationship", "understand", "disclose", "open up"]),
    ("cooperation", ["together", "help", "coordinate", "team", "work with"]),
]


def route_sotopia_dialogue(context: str, question: str) -> tuple[str, str]:
    combined = f"{context or ''} {question or ''}".lower()
    for scene_type, keywords in _DIALOGUE_SCENE_RULES:
        if any(kw in combined for kw in keywords):
            return scene_type, f"Context matched benchmark keywords -> {scene_type}"
    return "cooperation", "Default -> cooperation"
