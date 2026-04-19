"""SocialIQA benchmark-specific priors (clean release stub).

Hand-crafted per-question hints have been removed from the public repo;
only the empty interface is retained for backward-compat imports.
"""
from __future__ import annotations

from typing import Dict, List


def collect_socialiqa_priors(question: str, scene_type: str = "") -> Dict[str, List[str]]:
    return {}


def collect_socialiqa_reasoning_rules(question: str) -> List[str]:
    return []


def collect_socialiqa_calibration_examples(question: str) -> List[str]:
    return []
