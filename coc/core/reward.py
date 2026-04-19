"""
奖励计算
========
伪奖励（搜索阶段）和最终奖励（反馈阶段）。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def compute_pseudo_reward(
    chain: List[str],
    node_outputs: Dict[str, Dict[str, Any]],
    question: str = "",
    options: Optional[Dict[str, str]] = None,
    w_coherence: float = 0.4,
    w_fit: float = 0.3,
    w_convergence: float = 0.3,
) -> float:
    """
    伪奖励 r̃ = w1·Coh + w2·Fit + w3·Conv

    - Coh: 链内节点输出的逻辑一致性（后续节点是否引用前序输出）
    - Fit: 节点输出与问题的相关性
    - Conv: 答案是否成功收敛到某一候选选项
    """
    coh = _coherence_score(chain, node_outputs)
    fit = _relevance_score(chain, node_outputs, question)
    conv = _convergence_score(chain, node_outputs, options)

    reward = w_coherence * coh + w_fit * fit + w_convergence * conv
    return round(max(0.0, min(1.0, reward)), 4)


def compute_final_reward(
    predicted: str,
    correct_answer: Optional[str],
    pseudo_reward: float = 0.5,
) -> float:
    """
    最终奖励：
    - 有标签时：完全正确 1.0，错误 0.0
    - 无标签时：返回伪奖励
    """
    if not correct_answer:
        return pseudo_reward

    pred = (predicted or "").strip().upper()
    gold = correct_answer.strip().upper()

    if pred == gold:
        return 1.0
    return 0.0


def _coherence_score(
    chain: List[str],
    node_outputs: Dict[str, Dict[str, Any]],
) -> float:
    """
    一致性评分：检查后续节点是否引用了前序节点的关键输出。
    简单启发式：后续节点的输入中是否包含前序节点输出的关键词。
    """
    if len(chain) <= 1:
        return 0.5

    score = 0.0
    count = 0

    for i in range(1, len(chain)):
        prev_node = chain[i - 1]
        curr_node = chain[i]
        prev_output = node_outputs.get(prev_node, {})
        curr_output = node_outputs.get(curr_node, {})

        # 提取前序节点的关键内容
        prev_text = _flatten_output(prev_output).lower()
        curr_text = _flatten_output(curr_output).lower()

        if not prev_text or not curr_text:
            score += 0.3  # 缺失输出给中性分
            count += 1
            continue

        # 计算关键词重叠
        prev_words = set(re.findall(r"\w{3,}", prev_text))
        curr_words = set(re.findall(r"\w{3,}", curr_text))
        if prev_words:
            overlap = len(prev_words & curr_words) / len(prev_words)
            score += min(1.0, overlap * 2)  # 放大重叠信号
        else:
            score += 0.3
        count += 1

    return round(score / max(count, 1), 4)


def _relevance_score(
    chain: List[str],
    node_outputs: Dict[str, Dict[str, Any]],
    question: str,
) -> float:
    """
    相关性评分：节点输出与问题的关键词重叠度。
    """
    if not question:
        return 0.5

    q_words = set(re.findall(r"\w{3,}", question.lower()))
    if not q_words:
        return 0.5

    total_overlap = 0.0
    count = 0

    for node_id in chain:
        output = node_outputs.get(node_id, {})
        out_text = _flatten_output(output).lower()
        out_words = set(re.findall(r"\w{3,}", out_text))
        if out_words:
            overlap = len(q_words & out_words) / len(q_words)
            total_overlap += min(1.0, overlap)
        count += 1

    return round(total_overlap / max(count, 1), 4)


def _convergence_score(
    chain: List[str],
    node_outputs: Dict[str, Dict[str, Any]],
    options: Optional[Dict[str, str]],
) -> float:
    """
    收敛度评分：最终节点输出是否指向某个候选选项。
    """
    if not options or not chain:
        return 0.5

    # 取链上最后一个节点的输出
    last_output = node_outputs.get(chain[-1], {})
    last_text = _flatten_output(last_output).lower()

    if not last_text:
        return 0.2

    # 检查是否包含选项标签或文本
    for label, text in options.items():
        if label.lower() in last_text or text.lower().strip() in last_text:
            return 1.0

    # 部分匹配
    for label, text in options.items():
        words = set(re.findall(r"\w{3,}", text.lower()))
        if words:
            out_words = set(re.findall(r"\w{3,}", last_text))
            overlap = len(words & out_words) / len(words)
            if overlap > 0.5:
                return 0.7

    return 0.3


def _flatten_output(output: Dict[str, Any]) -> str:
    """将节点输出字典展平为文本"""
    if isinstance(output, str):
        return output
    parts = []
    for key, val in output.items():
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, list):
            parts.extend(str(v) for v in val)
        elif isinstance(val, dict):
            parts.append(str(val))
    return " ".join(parts)
