"""
节点价值容器
============
按 scene_type × node_id 维护条件 Q 值和访问次数 N。
支持 EMA 更新、软剪枝、JSON 持久化。
"""
from __future__ import annotations

import fcntl
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class NodeStats:
    """
    节点级经验价值统计。
    Q[scene_type][node_id] = 经验价值（EMA 更新）
    N[scene_type][node_id] = 访问次数
    """

    def __init__(
        self,
        initial_q: float = 0.5,
        alpha: float = 0.2,
        soft_prune_threshold: float = 0.25,
        min_visits_for_prune: int = 5,
    ):
        self._Q: Dict[str, Dict[str, float]] = {}
        self._N: Dict[str, Dict[str, int]] = {}
        self.initial_q = initial_q
        self.alpha = alpha  # EMA 学习率
        self.soft_prune_threshold = soft_prune_threshold
        self.min_visits_for_prune = min_visits_for_prune

    def value(self, scene: str, node: str) -> float:
        """获取节点在场景下的 Q 值"""
        return self._Q.get(scene, {}).get(node, self.initial_q)

    def visits(self, scene: str, node: str) -> int:
        """获取节点在场景下的访问次数"""
        return self._N.get(scene, {}).get(node, 0)

    def update(self, scene: str, chain: List[str], reward: float) -> Dict[str, Any]:
        """
        EMA 更新链上所有节点的 Q 值。
        Q(v) ← Q(v) + α * (reward - Q(v))
        返回更新详情。
        """
        details = {}
        if scene not in self._Q:
            self._Q[scene] = {}
        if scene not in self._N:
            self._N[scene] = {}

        for node in chain:
            old_q = self._Q[scene].get(node, self.initial_q)
            old_n = self._N[scene].get(node, 0)
            new_q = old_q + self.alpha * (reward - old_q)
            new_n = old_n + 1
            self._Q[scene][node] = round(new_q, 4)
            self._N[scene][node] = new_n
            details[node] = {
                "old_q": round(old_q, 4),
                "new_q": round(new_q, 4),
                "old_n": old_n,
                "new_n": new_n,
            }
        return details

    def ucb_score(
        self,
        scene: str,
        parent: str,
        child: str,
        c: float = 0.4,
        theory_prior: float = 0.0,
        memory_prior: float = 0.0,
        mu_theory: float = 0.6,
        nu_memory: float = 0.4,
    ) -> float:
        """
        UCB1 + 理论先验 + 记忆先验
        score = Q(c) + c * sqrt(ln(N_parent+1) / (N_c+1)) + μ * P_BDP + ν * P_Mem
        """
        q = self.value(scene, child)
        n_parent = max(self.visits(scene, parent), 1)
        n_child = self.visits(scene, child)

        exploitation = q
        exploration = c * math.sqrt(math.log(n_parent + 1) / (n_child + 1))
        prior_bonus = mu_theory * theory_prior + nu_memory * memory_prior

        return exploitation + exploration + prior_bonus

    def should_prune(self, scene: str, node: str) -> bool:
        """判断节点是否应被软剪枝"""
        n = self.visits(scene, node)
        q = self.value(scene, node)
        return n >= self.min_visits_for_prune and q < self.soft_prune_threshold

    def snapshot(self, scene: Optional[str] = None) -> Dict[str, Any]:
        """导出当前状态快照"""
        if scene:
            return {
                "Q": dict(self._Q.get(scene, {})),
                "N": dict(self._N.get(scene, {})),
            }
        return {"Q": {s: dict(v) for s, v in self._Q.items()},
                "N": {s: dict(v) for s, v in self._N.items()}}

    def load(self, path: Path) -> None:
        """从 JSON 文件加载"""
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self._Q = data.get("Q", {})
        self._N = {s: {k: int(v) for k, v in nv.items()} for s, nv in data.get("N", {}).items()}

    def save(self, path: Path) -> None:
        """Bug #6 fix: 带文件锁的保存，防止并发写损坏 JSON"""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps({"Q": self._Q, "N": self._N}, ensure_ascii=False, indent=2)
        with open(path, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(content)
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def top_nodes(self, scene: str, k: int = 5) -> List[tuple]:
        """返回场景下 Q 值最高的 k 个节点"""
        q_map = self._Q.get(scene, {})
        sorted_nodes = sorted(q_map.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:k]
