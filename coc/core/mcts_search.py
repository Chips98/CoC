"""
MCTS 搜索引擎
==============
在 BDP 推理树上用蒙特卡洛树搜索定位最优认知链 π*(x)。
支持 UCB1 选择（含理论先验+记忆先验）、渐进展宽、多种 rollout 策略、
路径一致性检查、回传更新、早停。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .bdp_tree import (
    BDP_EDGES, ROOT_CANDIDATES, TERMINAL_NODES, NEAR_TERMINAL_NODES,
    legal_children, is_leaf, is_near_terminal, validate_chain, node_display_name,
)
from .node_value import NodeStats
from .theory_prior import scene_prior


@dataclass
class SearchConfig:
    """搜索超参数，从 config.yaml 加载"""
    max_depth: int = 3
    num_simulations: int = 3
    lambda_explore: float = 0.4       # UCB 探索系数
    mu_theory: float = 0.6            # 理论先验权重
    nu_memory: float = 0.4            # 记忆先验权重
    confidence_threshold: float = 0.85 # 早停置信度阈值
    progressive_widening_k: float = 1.0
    rollout_strategy: str = "greedy"   # greedy / random / hybrid
    # 消融开关
    no_theory_prior: bool = False
    no_value_update: bool = False
    no_tree_search: bool = False
    no_memory_prior: bool = False
    no_progressive_widening: bool = False  # 关闭渐进展宽 → 立即展开全部 legal children
    no_soft_prune: bool = False             # D1：关闭软剪枝（公式 7），评估剪枝增益
    # Bug #2 fix: 评测期冻结 Q/N
    freeze_q_during_eval: bool = False


@dataclass
class SearchState:
    """单次搜索的运行时状态"""
    scene_type: str
    node_stats: NodeStats
    theory_prior: Dict[str, float]     # {node_id: P_BDP}
    memory_prior: Dict[str, float]     # {node_id: P_Mem}
    # 搜索过程中的记录
    expanded_children: Dict[str, List[str]] = field(default_factory=dict)
    visit_history: List[List[str]] = field(default_factory=list)
    best_chain: Optional[List[str]] = None
    best_score: float = -1.0
    search_log: List[Dict[str, Any]] = field(default_factory=list)
    # Bug #1 fix: 本轮搜索的临时统计（不写入全局 node_stats）
    _sim_visits: Dict[tuple, int] = field(default_factory=dict)
    _sim_rewards: Dict[tuple, float] = field(default_factory=dict)


def search_cognition_chain(
    state: SearchState,
    config: SearchConfig,
) -> Tuple[List[str], Dict[str, Any]]:
    """
    完整 MCTS 搜索流程。

    返回:
        (最优认知链, 搜索元数据)
    """
    # 消融：关闭树搜索时，直接用理论先验贪心选链
    if config.no_tree_search:
        chain = _greedy_by_prior(state, config)
        return chain, {"mode": "greedy_prior", "simulations": 0, "chains_explored": 1}

    for sim_idx in range(config.num_simulations):
        # ── 1. 选择起始 Ctx 节点 ──
        root = _select_root(state, config)
        chain = [root]

        # ── 2. 选择 + 展开 + 模拟 ──
        for depth in range(1, config.max_depth + 1):
            current = chain[-1]
            children = legal_children(current, depth - 1, config.max_depth)
            if not children:
                break
            children = _prefer_unvisited(children, chain)

            # 渐进展宽：控制子节点展开速度
            expanded = _get_or_expand(state, current, children, config)
            if not expanded:
                break

            # UCB 选择
            next_node = _ucb_select(state, current, expanded, config)
            chain.append(next_node)

            # 只有真正到达答案壳（option_filter / verify）才停止；
            # pragmatics / action_forecast 是 BDP 中间节点，必须继续向下扩展。
            if is_leaf(next_node):
                break

        # ── 3. 如果链未到达答案壳，用 rollout 补全；
        #       并强制保证链以 option_filter / verify 收尾 ──
        if chain[-1] not in TERMINAL_NODES:
            rollout_tail = _rollout(state, chain, config)
            chain.extend(rollout_tail)
        if chain[-1] not in TERMINAL_NODES:
            # rollout 之后仍未收口，强制追加 option_filter
            tail_children = BDP_EDGES.get(chain[-1], set())
            if "option_filter" in tail_children:
                chain.append("option_filter")
            elif "verify" in tail_children:
                chain.append("verify")
            else:
                chain.append("option_filter")

        # ── 4. 计算路径分数 ──
        path_score = _evaluate_path(state, chain, config)

        # ── 5. 回传更新（仅更新搜索树本地统计，不更新全局 node_stats） ──
        # Bug #1 fix: MCTS 内部只更新临时搜索统计，不触碰全局 Q/N。
        # 全局 Q/N 由 engine 在 compute_reward 后用 final_reward 更新一次。
        _backpropagate_local(state, chain, path_score)

        # ── 6. 记录 ──
        state.visit_history.append(chain)
        log_entry = {
            "simulation": sim_idx,
            "chain": chain,
            "chain_display": [node_display_name(n) for n in chain],
            "path_score": round(path_score, 4),
        }
        state.search_log.append(log_entry)

        if path_score > state.best_score:
            state.best_score = path_score
            state.best_chain = list(chain)

        # ── 7. 早停检查 ──
        if _should_stop_early(state, config, sim_idx):
            break

    # 最终输出
    final_chain = state.best_chain or _greedy_by_prior(state, config)
    metadata = {
        "mode": "mcts",
        "simulations": len(state.visit_history),
        "chains_explored": len(state.visit_history),
        "best_score": round(state.best_score, 4),
        "all_chains": [
            {"chain": h, "display": [node_display_name(n) for n in h]}
            for h in state.visit_history
        ],
        "search_log": state.search_log,
    }
    return final_chain, metadata


# ============================================================
# 内部函数
# ============================================================

def _select_root(state: SearchState, config: SearchConfig) -> str:
    """从 ROOT_CANDIDATES 中用 UCB 选择起始节点"""
    roots = list(ROOT_CANDIDATES)
    if len(roots) == 1:
        return roots[0]

    best_root = roots[0]
    best_score = -float("inf")

    for root in roots:
        tp = state.theory_prior.get(root, 0.3) if not config.no_theory_prior else 0.0
        mp = state.memory_prior.get(root, 0.0) if not config.no_memory_prior else 0.0
        score = state.node_stats.ucb_score(
            state.scene_type, "__root__", root,
            c=config.lambda_explore,
            theory_prior=tp,
            memory_prior=mp,
            mu_theory=config.mu_theory,
            nu_memory=config.nu_memory,
        )
        if score > best_score:
            best_score = score
            best_root = root

    return best_root


def _get_or_expand(
    state: SearchState,
    parent: str,
    all_children: List[str],
    config: SearchConfig,
) -> List[str]:
    """
    渐进展宽：只有当 N(parent) >= k * |expanded|^2 时才展开新子节点。
    防止在早期就把所有合法子节点全部展开。
    """
    key = parent
    if key not in state.expanded_children:
        state.expanded_children[key] = []

    expanded = state.expanded_children[key]
    n_parent = state.node_stats.visits(state.scene_type, parent)

    # 消融：no_progressive_widening 直接展开全部 legal children
    if config.no_progressive_widening:
        if not expanded:
            sorted_children = sorted(
                all_children,
                key=lambda c: state.theory_prior.get(c, 0.3),
                reverse=True,
            )
            state.expanded_children[key] = sorted_children
            return sorted_children
        return expanded

    # 渐进展宽条件
    k = config.progressive_widening_k
    max_expanded = max(1, int(math.sqrt(n_parent / k + 1)))

    if len(expanded) < len(all_children) and len(expanded) < max_expanded:
        # 按理论先验排序，优先展开高先验的子节点
        unexpanded = [c for c in all_children if c not in expanded]
        if unexpanded:
            unexpanded.sort(
                key=lambda c: state.theory_prior.get(c, 0.3),
                reverse=True,
            )
            expanded.append(unexpanded[0])
            state.expanded_children[key] = expanded

    return expanded if expanded else all_children[:1]


def _ucb_select(
    state: SearchState,
    parent: str,
    children: List[str],
    config: SearchConfig,
) -> str:
    """
    UCB1 选择：
    score(c) = Q(c) + λ·√(ln(N_parent+1)/(N_c+1)) + μ·P_BDP(c) + ν·P_Mem(c)
    """
    if len(children) == 1:
        return children[0]

    best_child = children[0]
    best_score = -float("inf")

    for child in children:
        # 软剪枝：跳过 Q 值过低的节点（D1 消融时关闭以评估其独立贡献）
        if not config.no_soft_prune and state.node_stats.should_prune(state.scene_type, child):
            continue

        tp = state.theory_prior.get(child, 0.3) if not config.no_theory_prior else 0.0
        mp = state.memory_prior.get(child, 0.0) if not config.no_memory_prior else 0.0

        score = state.node_stats.ucb_score(
            state.scene_type, parent, child,
            c=config.lambda_explore,
            theory_prior=tp,
            memory_prior=mp,
            mu_theory=config.mu_theory,
            nu_memory=config.nu_memory,
        )
        if score > best_score:
            best_score = score
            best_child = child

    return best_child


def _rollout(
    state: SearchState,
    chain_so_far: List[str],
    config: SearchConfig,
) -> List[str]:
    """
    从当前链末端 rollout 到终止节点。
    支持三种策略：greedy / random / hybrid
    """
    strategy = config.rollout_strategy
    tail: List[str] = []
    current = chain_so_far[-1]
    depth = len(chain_so_far) - 1

    for _ in range(config.max_depth - depth):
        children = legal_children(current, depth + len(tail), config.max_depth)
        if not children:
            break
        children = _prefer_unvisited(children, chain_so_far + tail)

        if strategy == "greedy":
            next_node = _greedy_pick(state, current, children, config)
        elif strategy == "random":
            next_node = random.choice(children)
        elif strategy == "hybrid":
            # 前半段贪心，后半段随机
            if len(tail) < (config.max_depth - depth) // 2:
                next_node = _greedy_pick(state, current, children, config)
            else:
                next_node = random.choice(children)
        else:
            next_node = _greedy_pick(state, current, children, config)

        tail.append(next_node)
        current = next_node

        if is_leaf(next_node):
            break

    return tail


def _greedy_pick(
    state: SearchState,
    parent: str,
    children: List[str],
    config: SearchConfig,
) -> str:
    """贪心选择：按 Q + 理论先验 + 记忆先验 选最优"""
    best = children[0]
    best_val = -float("inf")
    for c in children:
        q = state.node_stats.value(state.scene_type, c)
        tp = state.theory_prior.get(c, 0.3) if not config.no_theory_prior else 0.0
        mp = state.memory_prior.get(c, 0.0) if not config.no_memory_prior else 0.0
        val = q + config.mu_theory * tp + config.nu_memory * mp
        if val > best_val:
            best_val = val
            best = c
    return best


def _greedy_by_prior(state: SearchState, config: SearchConfig) -> List[str]:
    """消融模式：纯理论先验贪心选链"""
    chain = []
    # 选起始节点
    roots = list(ROOT_CANDIDATES)
    root = max(roots, key=lambda r: state.theory_prior.get(r, 0.3))
    chain.append(root)

    for depth in range(1, config.max_depth + 1):
        current = chain[-1]
        children = legal_children(current, depth - 1, config.max_depth)
        if not children:
            break
        children = _prefer_unvisited(children, chain)
        # 按理论先验贪心
        best = max(children, key=lambda c: state.theory_prior.get(c, 0.3))
        chain.append(best)
        if is_leaf(best):
            break

    return chain


def _prefer_unvisited(children: List[str], chain: List[str]) -> List[str]:
    """
    Prefer children that do not already appear in the current chain.
    If all children are already present, keep the original set as a safe fallback.
    """
    visited = set(chain)
    filtered = [child for child in children if child not in visited]
    return filtered if filtered else children


def _evaluate_path(state: SearchState, chain: List[str], config: SearchConfig) -> float:
    """
    路径评分：综合 Q 值均值 + 理论先验均值 + 链长度奖励 + 多样性奖励。
    这是搜索阶段的快速评分，不涉及 LLM 调用。
    """
    if not chain:
        return 0.0

    # Bug #5 fix: 不再用 q_mean 参与路径评分（避免 Q 值自引用循环）。
    # path_score 只由理论先验 + 记忆先验 + 结构特征决定。

    # 理论先验均值
    tp_sum = sum(state.theory_prior.get(n, 0.3) for n in chain)
    tp_mean = tp_sum / len(chain)

    # 记忆先验均值
    mp_sum = sum(state.memory_prior.get(n, 0.0) for n in chain)
    mp_mean = mp_sum / max(len(chain), 1)

    # 链长度奖励
    length_bonus = 0.0
    L = len(chain)
    if 5 <= L <= 6:
        length_bonus = 0.20
    elif L == 4:
        length_bonus = 0.10
    elif L == 3:
        length_bonus = 0.0
    elif L <= 2:
        length_bonus = -0.25
    elif L > 6:
        length_bonus = -0.05

    # 显式奖励链中包含 observation_track
    if "observation_track" in chain and state.scene_type in {
        "belief_reasoning", "knowledge_reasoning", "nonliteral_reasoning"
    }:
        length_bonus += 0.08

    # 多样性奖励
    from .bdp_tree import BDP_NODE_TYPE
    tags = set(BDP_NODE_TYPE.get(n, "") for n in chain)
    diversity = len(tags) / max(len(chain), 1)
    diversity_bonus = 0.1 * diversity

    # 终止奖励
    if chain[-1] in TERMINAL_NODES:
        terminal_bonus = 0.15
    elif chain[-1] in NEAR_TERMINAL_NODES:
        terminal_bonus = -0.05
    else:
        terminal_bonus = -0.15

    score = (
        0.45 * tp_mean
        + 0.15 * mp_mean
        + length_bonus
        + diversity_bonus
        + terminal_bonus
    )
    return max(0.0, min(1.0, score))


def _backpropagate_local(state: SearchState, chain: List[str], reward: float) -> None:
    """
    回传更新 — 仅更新搜索树的本地访问统计。
    Bug #1 fix: 不再调用 state.node_stats.update()（全局 Q/N），
    而是更新 SearchState 内部的 _sim_visits 和 _sim_rewards 用于 UCB 选择。
    全局 Q/N 只在 engine.py 的 compute_reward 之后更新一次。
    """
    for node in chain:
        key = (state.scene_type, node)
        state._sim_visits[key] = state._sim_visits.get(key, 0) + 1
        old_r = state._sim_rewards.get(key, 0.0)
        n = state._sim_visits[key]
        # 增量平均
        state._sim_rewards[key] = old_r + (reward - old_r) / n


def _should_stop_early(
    state: SearchState,
    config: SearchConfig,
    current_sim: int,
) -> bool:
    """
    早停条件：
    1. 至少完成 2 次模拟
    2. 最优链的平均 Q 值超过置信度阈值
    3. 最优链上所有节点的 N 值都 >= 2
    """
    if current_sim < 1:
        return False
    if state.best_chain is None:
        return False
    if state.best_score < config.confidence_threshold:
        return False

    # 检查最优链上所有节点的本轮搜索访问次数
    for node in state.best_chain:
        local_visits = state._sim_visits.get((state.scene_type, node), 0)
        if local_visits < 2:
            return False

    return True


def format_search_log(metadata: Dict[str, Any]) -> str:
    """格式化搜索日志，用于打印"""
    lines = []
    lines.append(f"搜索模式: {metadata.get('mode', '?')}")
    lines.append(f"模拟次数: {metadata.get('simulations', 0)}")
    lines.append(f"最优分数: {metadata.get('best_score', 0):.4f}")
    lines.append("")

    for entry in metadata.get("search_log", []):
        sim = entry.get("simulation", 0)
        display = " → ".join(entry.get("chain_display", []))
        score = entry.get("path_score", 0)
        lines.append(f"  模拟 #{sim}: {display}  (分数={score:.4f})")

    return "\n".join(lines)
