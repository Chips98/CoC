from __future__ import annotations

from typing import Any

from .text_utils import normalize_task_name


def infer_interaction_mode(task_input: dict[str, Any]) -> str:
    task_type = str(task_input.get("task_type", "")).lower()
    history = task_input.get("history") or []
    if task_type in {"multiple_choice_qa", "multiple_choice", "mcq"}:
        return "multiple_choice_qa"
    if task_type in {"single_turn_dialogue", "dialogue"}:
        return "single_turn_dialogue"
    if task_type in {"multi_turn_dialogue", "multi_turn_chat", "multi_agent_dialogue"}:
        return "multi_turn_dialogue"
    if "dialogue" in task_type:
        return "multi_turn_dialogue" if len(history) > 1 else "single_turn_dialogue"
    return "multiple_choice_qa"


def normalize_task_input(task_input: dict[str, Any], language: str) -> dict[str, Any]:
    normalized = dict(task_input)
    normalized["task_name"] = normalize_task_name(str(normalized.get("task_name", "unknown")))
    normalized.setdefault("task_type", "multiple_choice_qa")
    normalized.setdefault("task_description", "")
    normalized.setdefault("language", language)
    normalized.setdefault("context", "")
    normalized.setdefault("question", "")
    normalized.setdefault("options", {})
    normalized.setdefault("history", [])
    normalized.setdefault("meta", {})
    return normalized


def format_options(options: dict[str, str]) -> str:
    """格式化选项为文本"""
    if not options:
        return "(无选项)"
    return "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
