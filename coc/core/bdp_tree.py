"""
BDP 推理树 DAG 定义
===================
将 Belief-Desire Psychology 的因果链编译为有向无环图。
节点对应 BDP 原语，边对应因果依赖。
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

# ── 节点 → BDP 类型标签 ──
BDP_NODE_TYPE: Dict[str, str] = {
    # 预处理壳 (Ctx)
    "fact_extract":      "Ctx",
    "question_focus":    "Ctx",
    "constraint_parse":  "Ctx",
    # BDP 原语
    "observation_track": "P",    # 感知 Perception
    "knowledge_state":   "K",    # 知识 Knowledge
    "belief_state":      "B",    # 信念 Belief
    "emotion_desire":    "DE",   # 欲望+情绪 Desire/Emotion
    "intent_strategy":   "I",    # 意图 Intention
    "pragmatics":        "U",    # 语用 Utterance
    "action_forecast":   "A",    # 行为 Action
    # 答案整形壳
    "option_filter":     "Opt",
    "verify":            "Ver",
}

# 所有节点 ID
ALL_NODES: Tuple[str, ...] = tuple(BDP_NODE_TYPE.keys())

# BDP 原语节点（不含 Ctx 和 Ans 壳）
BDP_PRIMITIVES: Tuple[str, ...] = tuple(
    n for n, t in BDP_NODE_TYPE.items() if t not in ("Ctx", "Opt", "Ver")
)

# ── 因果 DAG 邻接表 ──
# 边来自 Wellman BDP 因果图 + 预处理/答案壳的连接规则
BDP_EDGES: Dict[str, Set[str]] = {
    # Ctx 节点可以指向任意 BDP 原语或答案壳
    "fact_extract": {
        "question_focus", "constraint_parse",
        "observation_track", "knowledge_state", "belief_state",
        "emotion_desire", "intent_strategy", "pragmatics",
        "action_forecast",
    },
    "question_focus": {
        "constraint_parse",
        "observation_track", "knowledge_state", "belief_state",
        "emotion_desire", "intent_strategy", "pragmatics",
        "action_forecast",
    },
    # 注：原本 constraint_parse → option_filter 的直边会让 MCTS 选出
    # 退化的 2-hop 链（root → option_filter），完全跳过 BDP 原语，导致
    # 大量 desire/intention/social_norm 任务被迫在没有 intent_strategy 的
    # 情况下作答。这里删除这条捷径，强制至少经过一个 BDP 原语。
    "constraint_parse": {
        "observation_track", "knowledge_state", "belief_state",
        "emotion_desire", "intent_strategy", "pragmatics", "action_forecast",
    },
    # BDP 因果依赖：P → K → B，B → DE，B → I，DE → I，I → A，I → U
    "observation_track": {"knowledge_state", "belief_state"},
    "knowledge_state":   {"belief_state", "emotion_desire"},
    "belief_state":      {"emotion_desire", "intent_strategy", "action_forecast"},
    "emotion_desire":    {"intent_strategy", "action_forecast"},
    "intent_strategy":   {"action_forecast", "pragmatics", "option_filter"},
    "pragmatics":        {"intent_strategy", "option_filter"},
    "action_forecast":   {"option_filter", "verify"},
    # 答案壳
    "option_filter":     {"verify"},
    "verify":            set(),
}

# 搜索起点（Ctx 节点）
ROOT_CANDIDATES: Tuple[str, ...] = ("fact_extract", "question_focus", "constraint_parse")

# 叶节点（答案壳）—— 真正的链终止点只有答案壳
LEAF_NODES: Set[str] = {"option_filter", "verify"}

# 可作为链终止的节点（**只**包含答案壳）。
# 注意：pragmatics(U) 与 action_forecast(A) 是 BDP 因果链上的中间节点，
# 必须可以继续衔接到 option_filter / verify，否则链会被腰斩成 2 节点退化形态。
TERMINAL_NODES: Set[str] = {"option_filter", "verify"}

# BDP 中间“近终态”节点（用于路径长度奖励，不再用于硬终止）
NEAR_TERMINAL_NODES: Set[str] = {"action_forecast", "pragmatics"}


def legal_children(node: str, depth: int, max_depth: int) -> List[str]:
    """
    给定当前节点和深度，返回合法子节点列表。

    规则：
      1) 普通深度返回所有合法子节点；
      2) 当 depth >= max_depth - 1 时，强制把链收口到答案壳
         （option_filter / verify），但若没有这种边，则放行所有 BDP 子节点
         以避免出现“无路可走 → 链停在中间”。
    """
    children = BDP_EDGES.get(node, set())
    if not children:
        return []

    if depth >= max_depth - 1:
        ans = [c for c in children if c in TERMINAL_NODES]
        if ans:
            return ans
        # 没有直接答案壳子节点，则退而允许 NEAR_TERMINAL，再退而允许全部
        near = [c for c in children if c in NEAR_TERMINAL_NODES]
        if near:
            return near

    return list(children)


def is_leaf(node: str) -> bool:
    """判断是否为真正的答案壳终止节点（不包含 pragmatics / action_forecast）"""
    return node in TERMINAL_NODES


def is_near_terminal(node: str) -> bool:
    """判断是否为 BDP 因果链上的近终态节点（pragmatics / action_forecast）"""
    return node in NEAR_TERMINAL_NODES


def is_answer_node(node: str) -> bool:
    """判断是否为答案整形节点"""
    return BDP_NODE_TYPE.get(node) in ("Opt", "Ver")


def validate_chain(chain: List[str]) -> bool:
    """验证一条链是否满足 DAG 约束"""
    if not chain:
        return False
    # 起点必须是 Ctx 节点
    if chain[0] not in ROOT_CANDIDATES:
        return False
    # 每条边必须在 DAG 中
    for i in range(len(chain) - 1):
        if chain[i + 1] not in BDP_EDGES.get(chain[i], set()):
            return False
    return True


def all_paths(max_depth: int = 3) -> List[List[str]]:
    """
    枚举所有合法路径（调试用）。
    从 ROOT_CANDIDATES 出发，深度不超过 max_depth。
    """
    results: List[List[str]] = []

    def _dfs(path: List[str], depth: int):
        current = path[-1]
        if is_leaf(current) or depth >= max_depth:
            results.append(list(path))
            return
        children = legal_children(current, depth, max_depth)
        if not children:
            results.append(list(path))
            return
        for child in children:
            path.append(child)
            _dfs(path, depth + 1)
            path.pop()

    for root in ROOT_CANDIDATES:
        _dfs([root], 0)

    return results


def node_display_name(node_id: str) -> str:
    """返回节点的显示名称，用于日志打印"""
    tag = BDP_NODE_TYPE.get(node_id, "?")
    return f"{node_id}[{tag}]"
