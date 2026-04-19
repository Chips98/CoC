from __future__ import annotations

from typing import Dict, Tuple


def apply_sotopia_heuristic(
    task_input: dict,
    current_answer: str,
    options: Dict[str, str],
) -> Tuple[str, str]:
    # Sotopia 当前没有多选项标签答案，这里只保留独立入口，后续放对话后处理规则。
    return current_answer, ""
