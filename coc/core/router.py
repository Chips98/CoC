"""
场景类型路由
============
将任务输入映射到 scene_type，不再输出 node_chain（chain 由 MCTS 决定）。
保留旧 task_parser.py 的映射逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..benchmarks.socialiqa.router import route_socialiqa
from ..benchmarks.sotopia.router import route_sotopia_dialogue


@dataclass
class RouteResult:
    """路由结果"""
    scene_type: str                    # 场景类型（对应 theory_prior 表的 key）
    task_name: str                     # 规范化后的任务名
    interaction_mode: str              # single_turn / dialogue
    benchmark_task: str = ""           # 原始 benchmark 子任务名
    ability: str = ""                  # 能力标签
    route_reason: str = ""             # 路由理由

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_type": self.scene_type,
            "task_name": self.task_name,
            "interaction_mode": self.interaction_mode,
            "benchmark_task": self.benchmark_task,
            "ability": self.ability,
            "route_reason": self.route_reason,
        }


# ── ToMBench benchmark_task → scene_type 映射 ──
_BENCHMARK_SCENE_MAP: Dict[str, str] = {
    "false belief task": "belief_reasoning",
    "scalar implicature test": "nonliteral_reasoning",
    "hinting task test": "nonliteral_reasoning",
    "strange story task": "nonliteral_reasoning",
    "faux-pas recognition test": "nonliteral_reasoning",
    "knowledge-attention links": "knowledge_reasoning",
    "knowledge-pretend play links": "knowledge_reasoning",
    "percepts-knowledge links": "knowledge_reasoning",
    "unexpected outcome test": "emotion_reasoning",
    "emotion regulation": "emotion_reasoning",
    "hidden emotions": "emotion_reasoning",
    "discrepant emotions": "emotion_reasoning",
    "moral emotions": "emotion_reasoning",
    "discrepant desires": "desire_reasoning",
    "multiple desires": "desire_reasoning",
    "discrepant intentions": "intention_reasoning",
    "prediction of actions": "planning_reasoning",
    "completion of failed actions": "planning_reasoning",
    "persuasion story task": "social_norm_reasoning",
    "ambiguous story task": "social_norm_reasoning",
}

def route_scene(task_input: Dict[str, Any], mode: str = "rule") -> RouteResult:
    """
    将任务输入路由到 scene_type。

    参数:
        task_input: 规范化后的任务输入
        mode: "rule"（规则路由）或 "llm"（LLM 路由，暂未实现）

    返回:
        RouteResult
    """
    task_name = str(task_input.get("task_name", "")).strip().lower()
    meta = task_input.get("meta", {})
    benchmark_task = str(meta.get("benchmark_task", "")).lower().strip()
    ability = str(meta.get("ability", "")).strip()
    question = str(task_input.get("question", "")).lower()
    context = str(task_input.get("context", "")).lower()
    history = task_input.get("history", [])

    # 推断交互模式
    interaction_mode = "dialogue" if history else "single_turn"

    # ── SocialIQA ──
    if task_name in ("socialiqa", "social_iqa"):
        scene_type, reason = route_socialiqa(question, task_input.get("options") or {})
        return RouteResult(
            scene_type=scene_type,
            task_name="socialiqa",
            interaction_mode="single_turn",
            benchmark_task=benchmark_task,
            ability=ability,
            route_reason=reason,
        )

    # ── Sotopia 对话 ──
    if task_name in ("sotopia", "dialogue") or interaction_mode == "dialogue":
        scene_type, reason = route_sotopia_dialogue(context, question)
        return RouteResult(
            scene_type=scene_type,
            task_name=task_name or "dialogue",
            interaction_mode="dialogue",
            benchmark_task=benchmark_task,
            ability=ability,
            route_reason=reason,
        )

    # ── ToMBench / SimpleToM / 其他 benchmark ──
    scene_type, reason = _route_benchmark(benchmark_task, question, context, ability)
    return RouteResult(
        scene_type=scene_type,
        task_name=task_name or "tombench",
        interaction_mode="single_turn",
        benchmark_task=benchmark_task,
        ability=ability,
        route_reason=reason,
    )

def _route_benchmark(
    benchmark_task: str, question: str, context: str, ability: str = ""
) -> tuple[str, str]:
    """Benchmark 路由：benchmark_task 主导 + 少量定向细分。"""
    ability_l = (ability or "").strip().lower()
    q = (question or "").strip().lower()

    if benchmark_task in _BENCHMARK_SCENE_MAP:
        scene_type = _BENCHMARK_SCENE_MAP[benchmark_task]

        # 注意：不再做“全局 ability 覆盖”。
        # ToMBench 的 ability 标签跨题型复用较多，强制覆盖会把
        # Unexpected Outcome / Strange Story / Persuasion 等题误路由。
        # 仅在少数已验证有效的子任务上做定向细分。

        # 1.6) Persuasion Story Task：'how does X persuade/convince' → intention_reasoning，
        # 让 intent_strategy 节点和说服策略税法生效。
        if benchmark_task == "persuasion story task":
            if any(kw in q for kw in ("how does", "how did", "how should", "怎么", "如何")):
                return "intention_reasoning", (
                    f"benchmark_task '{benchmark_task}' how-子题 → intention_reasoning"
                )

        # 1.7) Ambiguous Story Task：只在明确问“感觉/反应”且能力标签也指向
        # beliefs-based emotions 时，才切到 emotion_reasoning。
        # “what do you think ... thinks” 这类题仍默认 belief_reasoning。
        if benchmark_task == "ambiguous story task":
            if (
                "beliefs based action/emotions" in ability_l
                and (
                    "feel" in q
                    or "reaction" in q
                    or q.startswith("how does")
                    or q.startswith("how do")
                )
            ):
                return "emotion_reasoning", (
                    f"benchmark_task '{benchmark_task}' belief-emotion 子题 → emotion_reasoning"
                )

        # 2) why-类问题只在部分场景下偏向意图推理；
        #    避免把情绪题（如 Unexpected Outcome）误改路由。
        if q.startswith("why ") and scene_type in (
            "social_norm_reasoning",
            "planning_reasoning",
            "desire_reasoning",
        ):
            return "intention_reasoning", (
                f"benchmark_task '{benchmark_task}' → {scene_type}; "
                f"why 问题覆盖 → intention_reasoning"
            )

        # 3) ambiguous/persuasion 故事的 belief 问题降为 belief_reasoning
        if benchmark_task in ("ambiguous story task", "persuasion story task") and (
            "belief" in q or "think" in q or "thought" in q
        ):
            return "belief_reasoning", (
                f"benchmark_task '{benchmark_task}' belief 子问 → belief_reasoning"
            )

        return scene_type, f"benchmark_task '{benchmark_task}' → {scene_type}"

    # SimpleToM 启发式路由
    if "belief" in question or "think" in question or "know" in question:
        return "belief_reasoning", "问题含 belief/think/know → belief_reasoning"
    if "feel" in question or "emotion" in question:
        return "emotion_reasoning", "问题含 feel/emotion → emotion_reasoning"
    if "want" in question or "desire" in question:
        return "desire_reasoning", "问题含 want/desire → desire_reasoning"
    if "intend" in question or "plan" in question or "will" in question:
        return "intention_reasoning", "问题含 intend/plan/will → intention_reasoning"

    return "belief_reasoning", "默认 → belief_reasoning"
