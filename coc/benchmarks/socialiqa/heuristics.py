from __future__ import annotations

import re
from typing import Dict, Tuple


# ── 情感词表 ──
_POSITIVE_EMOTIONS = {"happy", "proud", "excited", "pleased", "satisfied", "grateful",
                      "relieved", "loved", "successful", "confident"}
_NEGATIVE_EMOTIONS = {"embarrassed", "ashamed", "sad", "angry", "upset", "frustrated",
                      "guilty", "anxious", "afraid", "scared", "uncomfortable", "awkward",
                      "sorry", "jealous", "hurt", "caught out", "bored"}
_NEUTRAL_EMOTIONS = {"surprised", "curious", "confused", "interested", "friendly", "welcome"}

# ── 社交积极触发词（之后通常是正面反应）──
_SOCIAL_POSITIVE_TRIGGERS = [
    "helped", "praised", "thanked", "complimented", "gave flowers", "gave a gift",
    "asked for help", "showed up", "saved", "surprised", "cooked", "volunteered",
    "donated", "listened", "supported", "encouraged", "offered"
]

# ── 社交消极触发词 ──
_SOCIAL_NEGATIVE_TRIGGERS = [
    "insulted", "yelled", "lied", "cheated", "hurt", "ignored", "rejected",
    "embarrassed", "mocked", "stole", "abandoned", "fired", "broke up"
]


def _context_sentiment(context: str) -> str:
    """Quick heuristic for context tone."""
    c = context.lower()
    pos_hits = sum(1 for t in _SOCIAL_POSITIVE_TRIGGERS if t in c)
    neg_hits = sum(1 for t in _SOCIAL_NEGATIVE_TRIGGERS if t in c)
    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"


def _count_emotion_options(options: Dict[str, str]) -> Tuple[int, int, int]:
    """Count positive / negative / neutral emotion options."""
    pos, neg, neu = 0, 0, 0
    for v in options.values():
        vl = v.lower()
        if any(e in vl for e in _POSITIVE_EMOTIONS):
            pos += 1
        elif any(e in vl for e in _NEGATIVE_EMOTIONS):
            neg += 1
        elif any(e in vl for e in _NEUTRAL_EMOTIONS):
            neu += 1
    return pos, neg, neu


def _is_action_option(text: str) -> bool:
    """Rough check whether an option describes an action rather than a state/trait."""
    verbs = r"\b(go|get|find|call|tell|ask|help|buy|take|check|look|try|make|say|start|leave|move|run|plan|work|use|give|see|put|bring)\b"
    return bool(re.search(verbs, text.lower()))


def apply_socialiqa_heuristic(
    task_input: dict,
    current_answer: str,
    options: Dict[str, str],
) -> Tuple[str, str]:
    """
    Post-processing heuristic for SocialIQA.

    Returns (new_answer, method_description).
    Returns ("", "") when the heuristic does not intervene.

    Design philosophy:
    - This heuristic ONLY overrides in very high-confidence cases.
    - It is meant to catch systematic error patterns, not to second-guess
      the LLM on every question.
    - Return ("", "") means "no override — keep LLM answer."
    """
    if not current_answer or not options:
        return "", ""

    question = str(task_input.get("question") or "").strip().lower()
    context = str(task_input.get("context") or "").strip().lower()

    current_text = options.get(current_answer, "").lower()

    # ── Rule 1: next-step question should prefer actions over emotions ──
    if ("want to do next" in question or "what will" in question or "what does" in question) \
            and "feel" not in question:
        # Count action vs state options
        action_options = [k for k, v in options.items() if _is_action_option(v)]
        non_action_options = [k for k, v in options.items() if not _is_action_option(v)]
        if len(action_options) == 1 and not _is_action_option(current_text):
            # Only one action option exists and current answer is a non-action
            # Only override if there's a clear mismatch
            pass  # too risky to override blindly; keep LLM answer

    # ── Rule 2: prerequisite question — prefer the option that names a specific need ──
    # (no reliable heuristic without semantic understanding; skip override)

    # ── Rule 3: "how would you describe" — do not select an action as characterization ──
    if question.startswith("how would you describe"):
        # If current answer is an action verb phrase, check if a better trait/adjective exists
        if _is_action_option(current_text):
            trait_options = [(k, v) for k, v in options.items() if not _is_action_option(v)]
            if len(trait_options) == 1:
                return trait_options[0][0], "socialiqa_heuristic:describe_prefers_trait"

    # Default: no intervention
    return "", ""
