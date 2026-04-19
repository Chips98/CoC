"""
BDP 理论先验（JSON 驱动，按基线隔离）
=====================================
将 Wellman ToM Scale 的发展顺序编码为按 scene_type 的节点权重表。
来源：Wellman & Liu 2004, Wellman 1990, Perner 1991

架构：
  - data/priors/socialiqa_theory.json  → SocialIQA 专属权重
  - data/priors/sotopia_theory.json    → Sotopia 专属权重
  - data/priors/tombench_theory.json   → ToMBench / SimpleToM 专属权重
  - 内置 _FALLBACK_TABLE 作为后备（保持向后兼容）

调用方：build_theory_prior(scene_type, node_ids, benchmark="tombench")
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .bdp_tree import BDP_NODE_TYPE

logger = logging.getLogger(__name__)

# ── JSON 文件路径 ──
_PRIORS_DIR = Path(__file__).resolve().parent.parent / "data" / "priors"

# ── 基线关键词 → JSON 文件名 ──
_BENCHMARK_JSON_MAP = {
    "socialiqa": "socialiqa_theory.json",
    "social_iqa": "socialiqa_theory.json",
    "sotopia": "sotopia_theory.json",
    "dialogue": "sotopia_theory.json",
    "tombench": "tombench_theory.json",
    "simple_tom": "tombench_theory.json",
    "simpletom": "tombench_theory.json",
}

# ── JSON 加载缓存 ──
_JSON_CACHE: Dict[str, Dict[str, Dict[str, float]]] = {}


def _load_json_table(benchmark: str) -> Dict[str, Dict[str, float]]:
    """按基线关键词加载对应的 JSON 权重表（带缓存）"""
    bench_key = str(benchmark or "").strip().lower()
    fname = _BENCHMARK_JSON_MAP.get(bench_key, "tombench_theory.json")

    if fname in _JSON_CACHE:
        return _JSON_CACHE[fname]

    json_path = _PRIORS_DIR / fname
    if not json_path.exists():
        logger.warning(f"theory_prior JSON 不存在: {json_path}，回退到内置表")
        _JSON_CACHE[fname] = {}
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        table = {k: v for k, v in data.get("scene_weights", {}).items() if isinstance(v, dict)}
        _JSON_CACHE[fname] = table
        return table
    except Exception as e:
        logger.error(f"加载 theory_prior JSON 失败: {json_path} — {e}")
        _JSON_CACHE[fname] = {}
        return {}


# ── 内置后备表（当 JSON 加载失败时使用，保持向后兼容）──
_FALLBACK_TABLE: Dict[str, Dict[str, float]] = {
    # ToMBench 推理场景
    "belief_reasoning": {
        "Ctx": 0.8, "P": 0.9, "K": 0.9, "B": 1.0,
        "DE": 0.3, "I": 0.5, "A": 0.4, "U": 0.2,
        "Opt": 0.7, "Ver": 0.6,
    },
    "knowledge_reasoning": {
        "Ctx": 0.8, "P": 1.0, "K": 1.0, "B": 0.7,
        "DE": 0.2, "I": 0.3, "A": 0.3, "U": 0.1,
        "Opt": 0.7, "Ver": 0.6,
    },
    "emotion_reasoning": {
        "Ctx": 0.7, "P": 0.4, "K": 0.4, "B": 0.6,
        "DE": 1.0, "I": 0.5, "A": 0.4, "U": 0.3,
        "Opt": 0.6, "Ver": 0.5,
    },
    "desire_reasoning": {
        "Ctx": 0.7, "P": 0.3, "K": 0.4, "B": 0.5,
        "DE": 1.0, "I": 0.6, "A": 0.5, "U": 0.2,
        "Opt": 0.6, "Ver": 0.5,
    },
    "intention_reasoning": {
        "Ctx": 0.7, "P": 0.4, "K": 0.5, "B": 0.7,
        "DE": 0.6, "I": 1.0, "A": 0.7, "U": 0.4,
        "Opt": 0.6, "Ver": 0.5,
    },
    "nonliteral_reasoning": {
        "Ctx": 0.8, "P": 0.4, "K": 0.5, "B": 0.7,
        "DE": 0.4, "I": 0.8, "A": 0.3, "U": 1.0,
        "Opt": 0.7, "Ver": 0.6,
    },
    "planning_reasoning": {
        "Ctx": 0.8, "P": 0.6, "K": 0.6, "B": 0.7,
        "DE": 0.5, "I": 0.9, "A": 1.0, "U": 0.3,
        "Opt": 0.7, "Ver": 0.6,
    },
    "social_norm_reasoning": {
        "Ctx": 0.8, "P": 0.5, "K": 0.6, "B": 0.6,
        "DE": 0.5, "I": 0.7, "A": 0.6, "U": 0.7,
        "Opt": 0.7, "Ver": 0.6,
    },
    # Sotopia 对话场景
    "cooperation": {
        "Ctx": 0.7, "P": 0.4, "K": 0.4, "B": 0.5,
        "DE": 0.6, "I": 0.8, "A": 0.7, "U": 0.7,
        "Opt": 0.5, "Ver": 0.4,
    },
    "conflict": {
        "Ctx": 0.7, "P": 0.5, "K": 0.5, "B": 0.7,
        "DE": 0.8, "I": 0.9, "A": 0.6, "U": 0.5,
        "Opt": 0.5, "Ver": 0.4,
    },
    "negotiation": {
        "Ctx": 0.7, "P": 0.4, "K": 0.5, "B": 0.6,
        "DE": 0.7, "I": 1.0, "A": 0.8, "U": 0.6,
        "Opt": 0.5, "Ver": 0.4,
    },
    "persuasion": {
        "Ctx": 0.7, "P": 0.4, "K": 0.5, "B": 0.7,
        "DE": 0.6, "I": 0.9, "A": 0.5, "U": 0.8,
        "Opt": 0.5, "Ver": 0.4,
    },
    "boundary_setting": {
        "Ctx": 0.7, "P": 0.5, "K": 0.5, "B": 0.6,
        "DE": 0.7, "I": 0.8, "A": 0.7, "U": 0.6,
        "Opt": 0.5, "Ver": 0.4,
    },
    "repair": {
        "Ctx": 0.7, "P": 0.5, "K": 0.5, "B": 0.6,
        "DE": 0.8, "I": 0.7, "A": 0.6, "U": 0.7,
        "Opt": 0.5, "Ver": 0.4,
    },
    "trust_building": {
        "Ctx": 0.7, "P": 0.4, "K": 0.5, "B": 0.7,
        "DE": 0.6, "I": 0.7, "A": 0.5, "U": 0.8,
        "Opt": 0.5, "Ver": 0.4,
    },
    "competition": {
        "Ctx": 0.7, "P": 0.5, "K": 0.5, "B": 0.6,
        "DE": 0.6, "I": 0.9, "A": 0.8, "U": 0.4,
        "Opt": 0.5, "Ver": 0.4,
    },
}

# 默认先验（未知场景类型时使用）
_DEFAULT_PRIOR: Dict[str, float] = {
    "Ctx": 0.7, "P": 0.5, "K": 0.5, "B": 0.6,
    "DE": 0.5, "I": 0.6, "A": 0.5, "U": 0.4,
    "Opt": 0.6, "Ver": 0.5,
}


def _get_table(scene_type: str, benchmark: str = "") -> Dict[str, float]:
    """
    按 benchmark 加载 JSON 权重表，在其中查找 scene_type。
    若 JSON 表中找不到 scene_type，再从内置后备表中查找。
    """
    if benchmark:
        json_table = _load_json_table(benchmark)
        if scene_type in json_table:
            return json_table[scene_type]

    # 后备：从内置表查找
    if scene_type in _FALLBACK_TABLE:
        return _FALLBACK_TABLE[scene_type]

    return _DEFAULT_PRIOR


def scene_prior(scene_type: str, node_id: str, benchmark: str = "") -> float:
    """
    查表返回节点在给定场景下的理论先验权重。
    先按 benchmark 查 JSON 文件，再查内置后备表。

    参数:
        scene_type: 场景类型字符串
        node_id:    BDP 节点 ID
        benchmark:  基线名称（"socialiqa" / "sotopia" / "tombench" 等）
    """
    tag = BDP_NODE_TYPE.get(node_id, "")
    table = _get_table(scene_type, benchmark)
    return table.get(tag, 0.3)


def build_theory_prior(
    scene_type: str,
    node_ids: List[str],
    benchmark: str = "",
) -> Dict[str, float]:
    """
    为一组节点构建理论先验字典。

    参数:
        scene_type: 路由结果的场景类型
        node_ids:   所有 BDP 节点 ID 列表
        benchmark:  基线名称（可选，传入后按基线 JSON 文件选权重）
    """
    return {nid: scene_prior(scene_type, nid, benchmark) for nid in node_ids}


def get_scene_types(benchmark: str = "") -> List[str]:
    """返回所有已注册的场景类型"""
    all_keys = set(_FALLBACK_TABLE.keys())
    if benchmark:
        json_table = _load_json_table(benchmark)
        all_keys |= set(json_table.keys())
    return sorted(all_keys)
