"""
Prompt builders for node-stage guide generation and answer-stage reasoning.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..benchmarks.socialiqa.prompt_profile import (
    build_socialiqa_answer_notes,
    build_socialiqa_answer_system_parts,
    build_socialiqa_question_type_notes,
    is_socialiqa_task,
)
from ..core.task_priors import (
    collect_task_priors,
    collect_benchmark_calibration_examples,
    collect_benchmark_reasoning_rules,
    format_priors_for_node,
    format_global_priors,
)

_SKILL_CACHE: Dict[str, str] = {}
_SKILL_BRIEF_CACHE: Dict[str, str] = {}


# ── Hard-coded BDP node descriptions (used in compact-shared answer layout)
# One to two sentences per node grounded in the BDP cognitive primitive plus
# the typical social-reasoning trap at that node. Shown to the answer-stage
# LLM as a theoretical scaffold; the sample-specific insight comes from the
# single shared LLM guide rendered below it.
_NODE_BDP_DESCRIPTION_EN: Dict[str, str] = {
    "fact_extract": (
        "Fact Extract [Ctx]: enumerate the characters, events, and explicit "
        "facts from the story verbatim, without inferring anything yet."
    ),
    "question_focus": (
        "Question Focus [Ctx]: pin down what the question is really asking — "
        "belief vs truth, inner vs expressed, speaker vs listener, "
        "specific target vs general."
    ),
    "constraint_parse": (
        "Constraint Parse [Ctx]: identify the structural constraints (false "
        "belief, limited perception, hidden emotion, faux-pas role) that "
        "govern which part of the story matters."
    ),
    "observation_track": (
        "Observation Track [P]: for each character, record what they "
        "perceived and when; a character can only know facts they saw, "
        "heard, or were told."
    ),
    "knowledge_state": (
        "Knowledge State [K]: derive from perceptual access what each "
        "character actually knows at the question's timepoint — hidden "
        "contamination, sealed boxes, and unseen events are NOT known."
    ),
    "belief_state": (
        "Belief State [B]: reconstruct the target character's mental model "
        "of the world from their last observed state; a missed event "
        "leaves the world unchanged in their belief."
    ),
    "emotion_desire": (
        "Emotion / Desire [DE]: infer felt emotion or desire from the "
        "character's goals, expectations, and concerns. Treat surface event "
        "valence with suspicion when the character worries about disruption."
    ),
    "intent_strategy": (
        "Intent / Strategy [I]: recover the practical GOAL behind an action "
        "or utterance, not its literal content or outcome — failed plans "
        "still had an intention."
    ),
    "pragmatics": (
        "Pragmatics [U]: pick the intended social meaning, not the literal "
        "sentence meaning; handle irony, sarcasm, hinting, and faux-pas by "
        "mapping speech acts to social moves."
    ),
    "action_forecast": (
        "Action Forecast [A]: predict the next action under the character's "
        "current beliefs and intentions — not under the narrator's ground "
        "truth."
    ),
    "option_filter": (
        "Option Filter [Opt]: eliminate options that mismatch prior-node "
        "facts; each rejection must cite one concrete mismatch. Do not "
        "default to option A."
    ),
    "verify": (
        "Verify [Ver]: re-read the question target and sanity-check the "
        "surviving option against story-grounded evidence; reject options "
        "that invent hidden causes not in the story."
    ),
}

_NODE_BDP_DESCRIPTION_ZH: Dict[str, str] = {
    "fact_extract": (
        "事实提取 [Ctx]：逐字罗列故事中的人物、事件与显式事实，暂不做任何推断。"
    ),
    "question_focus": (
        "问题聚焦 [Ctx]：明确问题真正问的是什么——信念还是真相，内心还是外在表达，"
        "说者还是听者，具体目标还是整体。"
    ),
    "constraint_parse": (
        "约束解析 [Ctx]：识别决定哪部分信息重要的结构约束——错误信念、认知局限、"
        "隐藏情感、失礼角色等。"
    ),
    "observation_track": (
        "感知追踪 [P]：逐角色记录他在何时看到或听到了什么——角色只能知道他亲历过的事。"
    ),
    "knowledge_state": (
        "知识状态 [K]：由感知访问推导出每个角色在问题时点实际知道什么；隐藏污染、"
        "密闭盒内容、未见事件均不在其知识范围内。"
    ),
    "belief_state": (
        "信念状态 [B]：基于目标角色最后观察到的状态重建其心智模型；"
        "错过的事件在其信念中未发生。"
    ),
    "emotion_desire": (
        "情感/欲望 [DE]：从角色的目标、预期、担忧推断其真实情感或欲望。"
        "当角色担心秩序被打乱时，正面事件也可能触发负面情绪。"
    ),
    "intent_strategy": (
        "意图/策略 [I]：还原行动或话语背后的实际目标，而非其字面内容或结果——"
        "失败的计划也有意图。"
    ),
    "pragmatics": (
        "语用推理 [U]：选取说话人的社交意图而非字面意思；处理反讽、讽刺、暗示、"
        "失礼，将言语行为映射到社交动作。"
    ),
    "action_forecast": (
        "行动预测 [A]：在角色当前信念与意图下预测下一步行动，而非在叙述者已知"
        "真相下预测。"
    ),
    "option_filter": (
        "选项筛选 [Opt]：剔除与前序节点事实不符的选项；每次排除必须引用一条"
        "具体矛盾。切勿默认选 A。"
    ),
    "verify": (
        "验证 [Ver]：重读问题目标，核查剩余选项是否有故事中的明确证据支撑；"
        "拒绝虚构隐藏动机的选项。"
    ),
}


def _get_bdp_description(node_id: str, language: str = "en") -> str:
    """Return the hard-coded BDP role description for a node."""
    table = _NODE_BDP_DESCRIPTION_ZH if (language or "").lower().startswith("zh") else _NODE_BDP_DESCRIPTION_EN
    return table.get(node_id, node_id)

_CONDITIONING_RULES: Dict[str, List[str]] = {
    "belief_state": ["observation_track", "knowledge_state"],
    "emotion_desire": ["belief_state", "knowledge_state"],
    "intent_strategy": ["emotion_desire", "belief_state"],
    "pragmatics": ["intent_strategy", "belief_state"],
    "action_forecast": ["intent_strategy", "belief_state", "emotion_desire"],
    "option_filter": ["intent_strategy", "action_forecast", "pragmatics"],
    "verify": ["option_filter", "action_forecast"],
}


def _normalize_skill_task_name(task_name: str) -> str:
    task = str(task_name or "").strip().lower()
    if task in {"social_iqa"}:
        return "socialiqa"
    return task


def resolve_skill_path(node_id: str, skills_dir: Path, task_name: str = "") -> Optional[Path]:
    normalized_task = _normalize_skill_task_name(task_name)
    candidates: List[Path] = []
    if normalized_task:
        candidates.append(skills_dir / normalized_task / node_id.replace("_", "-") / "SKILL.md")
    candidates.append(skills_dir / "common" / node_id.replace("_", "-") / "SKILL.md")
    candidates.append(skills_dir / node_id.replace("_", "-") / "SKILL.md")

    for path in candidates:
        if path.exists():
            return path
    return None


def load_skill_text(node_id: str, skills_dir: Path, task_name: str = "") -> str:
    """Load raw SKILL.md text for a node."""
    cache_key = f"{_normalize_skill_task_name(task_name)}::{node_id}"
    if cache_key in _SKILL_CACHE:
        return _SKILL_CACHE[cache_key]

    skill_path = resolve_skill_path(node_id=node_id, skills_dir=skills_dir, task_name=task_name)
    if skill_path is None:
        return ""

    text = skill_path.read_text(encoding="utf-8")
    _SKILL_CACHE[cache_key] = text
    return text


_HARD_RULE_MARKERS = ("CRITICAL", "ALWAYS", "NEVER", "Rule:", "rule:", "Pattern:", "Apply:", "Result:")
def _extract_section(text: str, header: str) -> str:
    pattern = rf"##\s*{re.escape(header)}[^\n]*\n(.*?)(?:\n##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_hard_rules(text: str) -> List[str]:
    """Pull out imperative rule lines from generic methodology sections only."""
    rules: List[str] = []
    for header in ("Methodology", "Pitfalls"):
        block = _extract_section(text, header)
        if not block:
            continue
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("-"):
                continue
            body = stripped[1:].strip()
            if any(marker in body for marker in _HARD_RULE_MARKERS):
                rules.append(body)
    return rules


def load_skill_brief(node_id: str, skills_dir: Path, task_name: str = "") -> str:
    """Extract a node brief with description + Node Role + critical hard-coded rules."""
    cache_key = f"{_normalize_skill_task_name(task_name)}::{node_id}"
    if cache_key in _SKILL_BRIEF_CACHE:
        return _SKILL_BRIEF_CACHE[cache_key]

    text = load_skill_text(node_id, skills_dir, task_name=task_name)
    if not text:
        return ""

    description = ""
    front_matter = re.search(r"^---\n(.*?)\n---", text, re.DOTALL | re.MULTILINE)
    if front_matter:
        desc_m = re.search(r"^description:\s*(.+)$", front_matter.group(1), re.MULTILINE)
        if desc_m:
            description = desc_m.group(1).strip().strip('"').strip("'")

    role_lines: List[str] = []
    role_block = re.search(r"##\s*Node Role\s*\n(.*?)(?:\n##\s|\Z)", text, re.DOTALL)
    if role_block:
        for line in role_block.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                role_lines.append(stripped[1:].strip())

    hard_rules = _extract_hard_rules(text)

    parts: List[str] = []
    if description:
        parts.append(description)
    if role_lines:
        parts.append(" ".join(role_lines[:2]))
    if hard_rules:
        # Keep brief compact — at most 4 strongest rules per node.
        parts.append("Key rules: " + " || ".join(hard_rules[:4]))
    brief = " ".join(parts).strip()
    _SKILL_BRIEF_CACHE[cache_key] = brief
    return brief


def _build_scene_header(
    scene_type: str,
    benchmark_task: str,
    ability: str,
    task_name: str,
) -> str:
    parts = []
    if scene_type:
        parts.append(f"scene_type = {scene_type}")
    if task_name:
        parts.append(f"task = {task_name}")
    if benchmark_task:
        parts.append(f"benchmark_task = {benchmark_task}")
    if ability:
        parts.append(f"ability = {ability}")
    if not parts:
        return ""
    return "## Scene Context\n" + "\n".join(f"- {p}" for p in parts) + "\n"


def _build_conditioning_hint(
    node_id: str, prior_outputs: Dict[str, Dict[str, Any]]
) -> str:
    rules = _CONDITIONING_RULES.get(node_id, [])
    available = [r for r in rules if r in prior_outputs]
    if not available:
        return ""
    bullets = "\n".join(
        f"- Use [{n}] as reference to avoid repeating blind spots."
        for n in available
    )
    return f"## Cross-Node References\n{bullets}\n"


def _format_prior_outputs(prior_outputs: Dict[str, Dict[str, Any]]) -> str:
    if not prior_outputs:
        return ""
    parts = []
    for node_id, output in prior_outputs.items():
        if isinstance(output, dict):
            text = json.dumps(output, ensure_ascii=False, indent=2)
        else:
            text = str(output)
        parts.append(f"### {node_id}\n{text}")
    return "\n\n".join(parts)


def _format_bullets(items: List[str]) -> str:
    if not items:
        return ""
    return "\n".join(f"- {item}" for item in items)


def _collect_chain_guides(
    chain: List[str],
    node_outputs: Dict[str, Dict[str, Any]],
) -> str:
    """Render the Node-stage plan as the guide block for the Answer stage.

    Plan-based design:
      - the chain, BDP role templates, scene rules, and benchmark rules
        all live in the Node prompt — they are NOT repeated here;
      - the Answer stage sees only the natural-language plan paragraph
        that the Node produced (stored in node_outputs[*]['plan']).
    """
    if not chain:
        return ""

    plan_text = ""
    for node_id in chain:
        out = node_outputs.get(node_id, {})
        if isinstance(out, dict):
            # New schema stores the plan under "plan"; keep a legacy
            # fallback so old cached results still render correctly.
            p = str(out.get("plan", "") or out.get("thinking_guide", "") or "").strip()
            if p:
                plan_text = p
                break

    if not plan_text:
        return ""
    return f"Reasoning plan from the prior planning pass:\n  {plan_text}"


def build_compact_guide_prompt(
    chain: List[str],
    context: str,
    question: str,
    options: Dict[str, str],
    skills_dir: Path,
    task_input: Optional[Dict[str, Any]] = None,
    scene_type: str = "",
) -> List[Dict[str, str]]:
    """
    Build the Node (planner) prompt: one LLM call that produces a
    high-level reasoning PLAN as a natural-language paragraph.

    The Node stage is the only place where the cognition-chain
    structure, skill briefs, scene rules, and benchmark rules are
    exposed to the LLM. The downstream Answer stage will see ONLY
    the plan paragraph — it does not need to know the chain again.

    Output contract: {"plan": "<~200-token English paragraph>"}
      - describes the key analytical points to check, in order
      - absorbs benchmark / scene rules into the plan prose
      - MUST NOT contain the final answer or the option labels
    """
    meta = (task_input or {}).get("meta") or {}
    scene_header = _build_scene_header(
        scene_type=scene_type,
        benchmark_task=str(meta.get("benchmark_task", "") or ""),
        ability=str(meta.get("ability", "") or ""),
        task_name=str((task_input or {}).get("task_name", "") or ""),
    )
    options_text = (
        "\n".join(f"{k}. {v}" for k, v in sorted(options.items())) if options else "(No options)"
    )

    # Per-node skill briefs (~1 line each) — keep the chain structure legible
    node_lines = []
    for node_id in chain:
        brief = load_skill_brief(
            node_id,
            skills_dir,
            task_name=str((task_input or {}).get("task_name", "") or ""),
        ) or "No description available."
        node_lines.append(f"- {node_id}: {brief}")

    priors = collect_task_priors(task_input or {}, scene_type or "") if task_input else {}
    global_priors_text = format_global_priors(priors) if priors else ""
    per_node_prior_parts = []
    for node_id in chain:
        text = format_priors_for_node(priors, node_id)
        if text:
            per_node_prior_parts.append(f"### {node_id}\n{text}")
    benchmark_rules_text = _format_bullets(
        collect_benchmark_reasoning_rules(task_input or {}, scene_type or "")
    ) if task_input else ""

    system_prompt = (
        "You are an assistant skilled in social cognition reasoning. "
        "Given a story, a question, and a suggested cognition chain of reasoning nodes, "
        "your job is to produce a concise REASONING PLAN as a single natural-language paragraph "
        "(roughly 150-250 tokens in English).\n\n"
        "The plan should:\n"
        "- outline the key analytical points to consider, roughly following the cognition chain;\n"
        "- ground each point in specific entities / events from THIS story;\n"
        "- integrate scene rules and benchmark rules as practical advice;\n"
        "- describe what to analyze — leave the actual reasoning to the answer stage;\n"
        "- avoid committing to any option label (A/B/C/D) yourself.\n\n"
        "Freedom clause: the cognition chain is a suggestion, not a rigid template. "
        "If a chain node does not fit this particular item, feel free to skip it. "
        "If the story is simple, the plan can be brief. Do not pad the plan just to follow the chain.\n\n"
        "Output strict JSON only. Schema:\n"
        "{\n"
        '  "plan": "<English paragraph>"\n'
        "}\n"
        "no think"
    )

    user_parts = []
    if scene_header:
        user_parts.append(scene_header)
    user_parts.append("## Task and Goal")
    user_parts.append(
        "Write a high-level reasoning plan (English paragraph) that the answer stage will follow."
    )
    user_parts.append("\n## Problem")
    user_parts.append(f"Situation:\n{context}\n")
    user_parts.append(f"Question:\n{question}\n")
    user_parts.append(f"Options:\n{options_text}\n")
    user_parts.append("## Suggested Cognition-Chain Nodes (in order)")
    user_parts.append("\n".join(node_lines))
    if global_priors_text:
        user_parts.append("## Global Task Priors")
        user_parts.append(global_priors_text)
    if per_node_prior_parts:
        user_parts.append("## Node-Specific Task Priors")
        user_parts.append("\n".join(per_node_prior_parts))
    if benchmark_rules_text:
        user_parts.append("## Benchmark Rules")
        user_parts.append(benchmark_rules_text)

    # Scene-critical hard rules (skip for SocialIQA which has its own profile)
    _cg_task_name = str((task_input or {}).get("task_name", "") or "").lower()
    if _cg_task_name not in ("socialiqa", "social_iqa"):
        scene_rules_text = _build_scene_critical_rules(scene_type)
        if scene_rules_text:
            user_parts.append("")
            user_parts.append(scene_rules_text)
            user_parts.append(
                "When writing the plan, weave the most relevant of the above rules "
                "naturally into the analytical steps — mention traps to watch for "
                "and principles to apply, but focus on the current story's specifics."
            )

        # Task-specific guidance (soft hint, 2026-04-17).
        task_hint = _build_task_specific_hint(task_input)
        if task_hint:
            user_parts.append("")
            user_parts.append("## Task-specific guidance (soft hint — use when it fits)")
            user_parts.append(task_hint)

    user_parts.append(
        "\nReturn JSON only. The plan is a single English paragraph. "
        "Do not list or choose any option label."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n".join(user_parts)},
    ]


# Clean release: hand-tuned per-scene rules removed. The interface is kept
# so callers remain valid; extend this dict if you want to inject your own
# scene-level priors.
_SCENE_CRITICAL_RULES: Dict[str, List[str]] = {}


def _build_scene_critical_rules(scene_type: str) -> str:
    rules = _SCENE_CRITICAL_RULES.get((scene_type or "").strip().lower(), [])
    if not rules:
        return ""
    bullets = "\n".join(f"- {r}" for r in rules)
    return (
        "## Critical Decision Rules (scene-specific hard priors)\n"
        "These rules override generic sentiment reading. Apply them before finalizing the answer.\n"
        f"{bullets}\n"
    )


# Clean release: per-benchmark_task plan-writing hints removed. Callers fall
# through to the generic plan prompt.
_BENCHMARK_TASK_PLAN_HINTS: Dict[str, str] = {}


def _build_task_specific_hint(task_input: Optional[Dict[str, Any]]) -> str:
    """Fetch the task-specific plan-writing hint for the current item."""
    if not task_input:
        return ""
    meta = task_input.get("meta") or {}
    bt = str(meta.get("benchmark_task", "") or "").strip().lower()
    if not bt:
        return ""
    return _BENCHMARK_TASK_PLAN_HINTS.get(bt, "")


def build_answer_prompt(
    context: str,
    question: str,
    options: Dict[str, str],
    chain: List[str],
    node_outputs: Dict[str, Dict[str, Any]],
    task_name: str = "",
    language: str = "en",
    task_input: Optional[Dict[str, Any]] = None,
    scene_type: str = "",
    enable_counterfactual: bool = False,
) -> List[Dict[str, str]]:
    """
    Build final-answer prompt with dual-pass reasoning:
    1) guided reasoning
    2) counterfactual reasoning
    """
    options_text = (
        "\n".join(f"{k}. {v}" for k, v in sorted(options.items())) if options else "(No options)"
    )
    interaction_mode = str((task_input or {}).get("task_type", "") or "").lower()
    is_dialogue_task = "dialogue" in interaction_mode or str(task_name or (task_input or {}).get("task_name", "")).strip().lower() in {"sotopia", "dialogue"}
    guide_text = _collect_chain_guides(chain, node_outputs)
    if not guide_text:
        guide_text = "- No node guide available; rely on direct reading of the question."

    global_priors_text = ""
    key_node_priors_text = ""
    benchmark_rules_text = ""
    if task_input is not None:
        priors = collect_task_priors(task_input, scene_type or "")
        global_priors_text = format_global_priors(priors)
        key_lines: List[str] = []
        for nid in chain:
            txt = format_priors_for_node(priors, nid)
            if txt:
                key_lines.append(f"### {nid}\n{txt}")
        key_node_priors_text = "\n".join(key_lines)
        benchmark_rules_text = _format_bullets(
            collect_benchmark_reasoning_rules(task_input, scene_type or "")
        )

    meta = (task_input or {}).get("meta") or {}
    scene_header = _build_scene_header(
        scene_type=scene_type,
        benchmark_task=str(meta.get("benchmark_task", "") or ""),
        ability=str(meta.get("ability", "") or ""),
        task_name=task_name or str((task_input or {}).get("task_name", "") or ""),
    )

    _effective_task_name = task_name or str((task_input or {}).get("task_name", "") or "")
    _is_socialiqa = is_socialiqa_task(_effective_task_name)

    # ── System prompt ────────────────────────────────────────────────────────
    if _is_socialiqa:
        # SocialIQA keeps its specialized profile (rules baked into skills).
        system_parts = build_socialiqa_answer_system_parts(enable_counterfactual)
    elif is_dialogue_task:
        system_parts = [
            "You are a social dialogue agent for a multi-turn interaction benchmark (Sotopia).",
            "Your job: produce the character's EXACT next spoken line — not a plan, not coaching, not a stage direction.",
            "CRITICAL FORMAT RULES:",
            "- The 'reply' field must be the literal first-person utterance the character will say.",
            "- NEVER write 'X should say...', 'The best move is...', 'X should acknowledge...', or any third-person coaching.",
            "- NEVER write option labels (A/B/C) in the reply.",
            "- Write as if you ARE the character speaking right now.",
            "- The reply must be short (1-3 sentences), natural, and directly respondent to the partner's last message.",
            "Output JSON only with keys: guided_thought, reply.",
        ]
    else:
        # Plan-based answer stage — no chain / BDP / scene / benchmark rules
        # are injected here; those all live in the Node (planner) prompt.
        system_parts = [
            "You are an assistant skilled in social cognition reasoning.",
            "Follow the given reasoning plan step by step to analyze the story, "
            "then output the best option label.",
            "Output strict JSON only.",
        ]
    system_prompt = "\n".join(system_parts) + "\nno think"

    # ── User prompt ──────────────────────────────────────────────────────────
    user_parts = []

    # SocialIQA keeps its scene header + Cognition Chain Analysis block.
    if _is_socialiqa:
        if scene_header:
            user_parts.append(scene_header)
        user_parts.append("## Task and Objective")
        user_parts.append(
            "Solve the problem with guided reasoning only, then provide one final answer."
        )
        user_parts.append("\n## Problem")
        user_parts.append(f"Situation:\n{context}\n")
        user_parts.append(f"Question:\n{question}\n")
        user_parts.append(f"Options:\n{options_text}\n")
        user_parts.append("## Cognition Chain Analysis")
        user_parts.append("(Use this in your guided_thought pass. It may contain useful insights, but always verify against the story.)")
        user_parts.append(guide_text)
    elif is_dialogue_task:
        # Dialogue agents still read the plan as their "inner thought".
        user_parts.append("## Problem")
        user_parts.append(f"Situation:\n{context}\n")
        user_parts.append(f"Question:\n{question}\n")
        user_parts.append(f"Options:\n{options_text}\n")
        user_parts.append("## Reasoning Plan")
        user_parts.append(guide_text)
    else:
        # Plan-based main path — minimal prompt, plan-centric.
        user_parts.append("## Problem")
        user_parts.append(f"Situation:\n{context}\n")
        user_parts.append(f"Question:\n{question}\n")
        user_parts.append(f"Options:\n{options_text}\n")
        user_parts.append("## Reasoning Plan")
        user_parts.append(guide_text)

    if _is_socialiqa:
        user_parts.append("\n".join(build_socialiqa_answer_notes(enable_counterfactual)))
        question_type_notes = build_socialiqa_question_type_notes(question)
        if question_type_notes:
            user_parts.append("\n".join(question_type_notes))
    elif is_dialogue_task:
        available_actions = ((task_input or {}).get("meta") or {}).get("available_actions") or []
        available_actions_text = ", ".join(str(item) for item in available_actions) if available_actions else "unknown"
        agent_name = ((task_input or {}).get("meta") or {}).get("agent_name", "the character")
        agent_goal = str(((task_input or {}).get("meta") or {}).get("goal", "")).strip()
        turn_number = int(((task_input or {}).get("meta") or {}).get("turn_number", 0) or 0)

        # ── Inject dialogue history for context ──
        history = (task_input or {}).get("history") or []
        if history:
            user_parts.append("\n## Conversation History")
            for h in history[-8:]:  # last 8 turns
                role = h.get("role", "?") if isinstance(h, dict) else "?"
                content = h.get("content", str(h)) if isinstance(h, dict) else str(h)
                user_parts.append(f"[{role}]: {content[:300]}")

            # ── Anti-repetition: show agent's own recent messages ──
            own_msgs = [str(h.get("content", ""))[:150] for h in history[-6:]
                        if isinstance(h, dict) and str(h.get("role", "")).lower() == agent_name.lower()]
            if own_msgs:
                user_parts.append("\n## Your Recent Messages (DO NOT REPEAT)")
                for msg in own_msgs:
                    user_parts.append(f"- \"{msg}\"")
                user_parts.append("Your next reply MUST be substantially different from the above.")

        # ── Goal and turn context ──
        if agent_goal:
            user_parts.append(f"\n## Your Goal\n{agent_goal[:300]}")
        user_parts.append(f"\n## Turn Info\nYou are {agent_name}. Turn {turn_number}. Available actions: {available_actions_text}.")

        user_parts.append("\n## FORMAT RULES")
        user_parts.append(f"- The 'reply' field must be what {agent_name} SAYS RIGHT NOW, in first person.")
        user_parts.append("- WRONG: 'Alex should express interest...' (coaching/stage direction)")
        user_parts.append("- RIGHT: 'I'm really interested, could you go a bit lower?' (actual speech)")
        user_parts.append("\n## Notes")
        user_parts.append("- 1-3 sentences. Natural, direct, first-person speech.")
        user_parts.append("- Directly respond to what the partner just said.")
        user_parts.append("- If the partner rejected your request, do NOT repeat it — change your approach.")
        user_parts.append("- No revenge, threats, or social norm violations.")
        user_parts.append("- The reply must be paste-ready dialogue, not instructions or plans.")
    else:
        user_parts.append("\n## Notes")
        user_parts.append(
            "- Work through the plan step by step. Record your stepwise analysis "
            "in `guided_thought` (around 400-600 English tokens)."
        )
        user_parts.append(
            "- Ground each elimination in the option text itself. Do not invent "
            "motives, objects, or social injuries that are not supported by the story."
        )
        user_parts.append("- `final_answer` must be an option label (A/B/C/D).")

    user_parts.append("\n## Output Example")
    if is_dialogue_task:
        user_parts.append(
            "{\n"
            '  "guided_thought": "They seem hesitant, so I should acknowledge their concern and propose a concrete compromise.",\n'
            '  "reply": "I understand where you are coming from. How about we meet halfway on this?"\n'
            "}"
        )
    else:
        user_parts.append(
            "{\n"
            '  "guided_thought": "Step 1 (per plan): ... Step 2: ... Therefore option B is eliminated because ...",\n'
            '  "guided_answer": "A",\n'
            '  "final_answer": "A"\n'
            "}"
        )

    user_parts.append("\n## Output Format")
    if is_dialogue_task:
        user_parts.append(
            "Return strict JSON with exactly these 2 keys: guided_thought, reply."
        )
    else:
        user_parts.append(
            "Return strict JSON with exactly these 3 keys: "
            "guided_thought, guided_answer, final_answer."
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n".join(user_parts)},
    ]


def build_calibration_prompt(
    context: str,
    question: str,
    options: Dict[str, str],
    first_answer: str,
    first_reasoning: str,
    language: str = "en",
    first_pass_json: Optional[Dict[str, Any]] = None,
    task_input: Optional[Dict[str, Any]] = None,
    scene_type: str = "",
) -> List[Dict[str, str]]:
    """
    Build conflict-check prompt.
    Triggered only when guided and counterfactual answers disagree.
    """
    options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
    first_json_text = (
        json.dumps(first_pass_json, ensure_ascii=False, indent=2)
        if first_pass_json else "{}"
    )
    benchmark_rules_text = _format_bullets(
        collect_benchmark_reasoning_rules(task_input or {}, scene_type or "")
    ) if task_input else ""
    calibration_examples_text = _format_bullets(
        collect_benchmark_calibration_examples(task_input or {})
    ) if task_input else ""

    system_prompt = (
        "You are a reasoning verifier.\n"
        "The two initial passes produced conflicting answers.\n"
        "Reconcile the conflict and output one final answer.\n"
        "Verification policy:\n"
        "1) Keep the original problem facts fixed.\n"
        "2) Treat guided and counterfactual as two candidate hypotheses, not as 'trusted' versus 'suspect' by default.\n"
        "3) Only reject a hypothesis if it changes explicit facts, timeline, speaker identity, quoted content, or the question target.\n"
        "4) If both hypotheses keep the facts fixed, choose the one whose answer better matches the option semantics, benchmark rules, and concrete story evidence.\n"
        "4a) Do not prefer one side only because it sounds simpler or more generic. Prefer the side whose option text is more directly licensed by the story and the question target.\n"
        "5) It is valid for the counterfactual side to win when it is fact-consistent and explains the item better.\n"
        "6) First decide whether guided or counterfactual is the better hypothesis. Only use neither if both hypotheses are weak or fact-inconsistent and you must independently re-judge the options.\n"
        "7) If you choose guided or counterfactual, final_answer must exactly match that chosen hypothesis answer label.\n"
        "Output JSON only with exactly 3 keys:\n"
        '{ "selected_hypothesis": "guided|counterfactual|neither", "final_answer": "...", "verification_reason": "..." }\n'
        "Keep verification_reason around 100 tokens.\n"
        "no think"
    )

    first_guided = str((first_pass_json or {}).get("guided_answer", "")).strip()
    first_counterfactual = str((first_pass_json or {}).get("counterfactual_answer", "")).strip()
    first_guided_thought = str((first_pass_json or {}).get("guided_thought", "")).strip()
    first_counterfactual_thought = str((first_pass_json or {}).get("counterfactual_thought", "")).strip()
    if first_guided_thought:
        first_guided_thought = first_guided_thought[:1200]
    if first_counterfactual_thought:
        first_counterfactual_thought = first_counterfactual_thought[:900]

    user_prompt = (
        "## Task and Objective\n"
        "Resolve the contradiction between guided and counterfactual answers.\n\n"
        "## Problem\n"
        f"Situation:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        f"Options:\n{options_text}\n\n"
        "## Candidate Hypotheses\n"
        f"Guided answer label: {first_guided}\n"
        f"Guided thought summary:\n{first_guided_thought or '(missing)'}\n\n"
        f"Counterfactual answer label: {first_counterfactual}\n"
        f"Counterfactual thought summary:\n{first_counterfactual_thought or '(missing)'}\n\n"
        "## Parsed First-Pass JSON\n"
        f"{first_json_text}\n\n"
        + (
            "## Benchmark Rules\n"
            f"{benchmark_rules_text}\n\n"
            if benchmark_rules_text else ""
        )
        + (
            "## Calibration Examples\n"
            f"{calibration_examples_text}\n\n"
            if calibration_examples_text else ""
        )
        +
        (
            "## Reference Raw Output\n"
            f"{first_reasoning[:1200]}\n\n"
            if not first_pass_json else ""
        )
        +
        "Return JSON only. In verification_reason, state whether each side kept the original facts fixed, and why the winning answer better matches the item. "
        "Do not justify the winner with 'fewer assumptions' alone; tie it to the exact option wording and the concrete story evidence."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
