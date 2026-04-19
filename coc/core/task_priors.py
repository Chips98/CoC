"""
Task-level prior interface (P_TASK).

In the paper we describe P_TASK as a lightweight hook that can inject
benchmark-aware hints into specific BDP nodes. In this reference
implementation we keep only a single generic prior that applies to every
sample and every benchmark.  The original research repo shipped
hand-crafted per-benchmark / per-ability lookup tables; those are
intentionally removed here to keep the published code free from
benchmark-specific tuning.

Public API (consumed by prompts/node_prompts.py and core/answer_generator.py):

    collect_task_priors(task_input, scene_type)       -> Dict[node_id, List[str]]
    format_priors_for_node(priors, node_id)           -> str
    format_global_priors(priors)                      -> str
    collect_benchmark_reasoning_rules(task_input, ..) -> List[str]
    collect_benchmark_calibration_examples(task_input)-> List[str]
"""
from __future__ import annotations

from typing import Any, Dict, List


_GENERIC_PRIOR: List[str] = [
    "Answer only for the character, object, or time point explicitly asked "
    "about; do not substitute a different participant just because they "
    "feel more salient.",
]


def collect_task_priors(
    task_input: Dict[str, Any], scene_type: str
) -> Dict[str, List[str]]:
    """Return {node_id -> [hint, ...]} for prompt injection.

    The `_global` key is appended to the answer-stage system prompt.
    """
    return {"_global": list(_GENERIC_PRIOR)}


def format_priors_for_node(priors: Dict[str, List[str]], node_id: str) -> str:
    items = priors.get(node_id, [])
    if not items:
        return ""
    return "\n".join(f"- {item}" for item in items)


def format_global_priors(priors: Dict[str, List[str]]) -> str:
    return format_priors_for_node(priors, "_global")


def collect_benchmark_reasoning_rules(
    task_input: Dict[str, Any], scene_type: str = ""
) -> List[str]:
    """Benchmark-specific reasoning rules. Empty in the clean release."""
    return []


def collect_benchmark_calibration_examples(
    task_input: Dict[str, Any],
) -> List[str]:
    """Benchmark-specific calibration examples. Empty in the clean release."""
    return []
