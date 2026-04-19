"""
记忆先验
========
从检索到的相似成功案例中统计节点使用频率，构建 P_Mem(v|x)。
"""
from __future__ import annotations

from typing import Dict, List


def build_memory_prior(
    retrieved_cases: List[Dict],
    similarity_key: str = "similarity",
    chain_key: str = "chain",
) -> Dict[str, float]:
    """
    对 top-k 成功案例，统计它们的 chain 中各节点出现频率，
    按相似度加权归一化，返回 {node_id: prior_weight}。

    参数:
        retrieved_cases: 检索到的案例列表，每个案例包含 chain 和 similarity
        similarity_key: 相似度字段名
        chain_key: 认知链字段名

    返回:
        {node_id: 归一化权重}，权重范围 [0, 1]
    """
    if not retrieved_cases:
        return {}

    weighted_counts: Dict[str, float] = {}
    total_weight = 0.0

    for case in retrieved_cases:
        chain = case.get(chain_key, [])
        sim = float(case.get(similarity_key, 0.5))
        if not chain:
            continue
        for node_id in chain:
            weighted_counts[node_id] = weighted_counts.get(node_id, 0.0) + sim
        total_weight += sim

    if total_weight == 0:
        return {}

    # 归一化到 [0, 1]
    max_val = max(weighted_counts.values()) if weighted_counts else 1.0
    return {
        node_id: round(count / max_val, 4)
        for node_id, count in weighted_counts.items()
    }


def merge_priors(
    theory_prior: Dict[str, float],
    memory_prior: Dict[str, float],
    mu: float = 0.6,
    nu: float = 0.4,
) -> Dict[str, float]:
    """
    合并理论先验和记忆先验。
    merged(v) = μ * P_BDP(v) + ν * P_Mem(v)
    """
    all_nodes = set(theory_prior.keys()) | set(memory_prior.keys())
    merged = {}
    for node in all_nodes:
        tp = theory_prior.get(node, 0.0)
        mp = memory_prior.get(node, 0.0)
        merged[node] = round(mu * tp + nu * mp, 4)
    return merged
