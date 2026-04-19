from __future__ import annotations

from typing import List


def is_socialiqa_task(task_name: str) -> bool:
    return str(task_name or "").strip().lower() in {"socialiqa", "social_iqa"}


def build_socialiqa_answer_system_parts(enable_counterfactual: bool) -> List[str]:
    """V1-style minimal system prompt — keep the LLM's attention on the question, not on rules."""
    system_parts = [
        "You are a social reasoning expert answering a 3-choice social question.",
        "A cognition chain analysis is provided as background reference — use it if helpful, but reason independently.",
        "Pick the most natural, common-sense answer. Do not overthink.",
        "Output JSON only.",
    ]
    return system_parts


def build_socialiqa_answer_notes(enable_counterfactual: bool) -> List[str]:
    """V1-style minimal notes — let the LLM reason freely instead of constraining it."""
    notes = [
        "## Notes",
        "- Give at most two short reasoning sentences in guided_thought, then pick the answer.",
        "- Answer with the option label (A/B/C).",
    ]
    return notes


def build_socialiqa_question_type_notes(question: str) -> List[str]:
    """V1-style: one concise hint per question type, not multi-line rules."""
    q = str(question or "").strip().lower()
    notes: List[str] = []

    if "before this" in q:
        notes.append("- Prerequisite question: choose the necessary step before the event, not a result or background fact.")
    elif q.startswith("why did") or q.startswith("why would") or q.startswith("why does") or q.startswith("why was") or q.startswith("why is"):
        notes.append("- Motive question: choose the direct cause of the action, not a downstream effect or paraphrase.")
    elif q.startswith("what will happen to"):
        notes.append("- Consequence question: choose the most immediate outcome for the named person.")
    elif "want to do next" in q or q.startswith("what will") or q.startswith("what does"):
        notes.append("- Next-step question: choose the most ordinary immediate action under the situation.")
    elif q.startswith("how would you describe"):
        notes.append("- Describe question: choose the simplest supported characterization from the event.")
    elif "feel" in q:
        notes.append("- Feeling question: choose the target person's most direct subjective reaction.")
    elif "what should" in q or "best way" in q:
        notes.append("- Should/best-way question: choose the option that is both useful and socially fitting.")

    return notes
