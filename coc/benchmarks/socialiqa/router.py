from __future__ import annotations

import re


_SOCIALIQA_EMOTION_OPTION_MARKERS = {
    "embarrassed",
    "ashamed",
    "sad",
    "angry",
    "upset",
    "happy",
    "excited",
    "frustrated",
    "proud",
    "sorry",
    "guilty",
    "anxious",
    "afraid",
    "scared",
    "bored",
    "caught out",
    "loved",
    "welcome",
    "uncomfortable",
    "awkward",
    "relieved",
    "jealous",
    "hurt",
    "successful",
    "friendly",
}


def route_socialiqa(question: str, options: dict | None = None) -> tuple[str, str]:
    """
    将 SocialIQA 问题映射到细粒度 scene_type。

    Scene types（按优先级检查）:
    - emotion_reasoning     : 感受/情绪类 ("how does X feel", "feel after")
    - intention_reasoning   : 动机/原因类 ("why did", "why would")
    - prerequisite_reasoning: 前提类 ("before this", "need to do before")
    - consequence_reasoning : 后果类 ("what will happen to", "what will Others")
    - next_action_reasoning : 下一步行动类 ("want to do next", "what will X do", "what does X need")
    - social_norm_reasoning : 规范/描述类 ("how would you describe", "what should", "best way")
    - planning_reasoning    : 通用回退（旧类型保留兼容性）
    """
    q = str(question or "").lower().strip()
    options_blob = " ".join(str(v or "").strip().lower() for v in (options or {}).values())

    # ── 1. emotion_reasoning ──
    # "how does X feel" / "how will X feel" / "feel after" / "feel about"
    if re.search(r"\b(how does|how will|how would)\b.{0,30}\bfeel\b", q):
        return "emotion_reasoning", "How-feel regex -> emotion_reasoning"
    if any(kw in q for kw in ("feel as a result", "feel afterwards", "feel after",
                               "feel about", "feel like", " feel")):
        return "emotion_reasoning", "Feel keyword -> emotion_reasoning"
    # "how would you describe" with emotion/state option words
    if q.startswith("how would you describe") and any(
        marker in options_blob for marker in _SOCIALIQA_EMOTION_OPTION_MARKERS
    ):
        return "emotion_reasoning", "Describe + emotion options -> emotion_reasoning"

    # ── 2. intention_reasoning ──
    if re.search(r"^\s*why (did|would|does|is|was|were)\b", q):
        return "intention_reasoning", "Why-question -> intention_reasoning"

    # ── 3. prerequisite_reasoning ──
    # "before this", "need to do before", "did X do before"
    if re.search(r"\b(before this|need to do before|did .{1,30} do before|have to do before)\b", q):
        return "prerequisite_reasoning", "Before-this pattern -> prerequisite_reasoning"

    # ── 4. consequence_reasoning ──
    # "what will happen to X", "what will Others feel/do" when it's a consequence question
    if re.search(r"\bwhat will happen to\b", q):
        return "consequence_reasoning", "What-will-happen-to -> consequence_reasoning"
    if re.search(r"\bwhat happens? to\b", q):
        return "consequence_reasoning", "What-happens-to -> consequence_reasoning"

    # ── 5. social_norm_reasoning ──
    # "what should" is normative — must be checked BEFORE next_action "what will X do"
    if any(kw in q for kw in ("what should", "best way", "what is the best", "what is the right")):
        return "social_norm_reasoning", "Norm/should keyword -> social_norm_reasoning"
    if "how would you describe" in q:
        return "social_norm_reasoning", "Describe keyword -> social_norm_reasoning"

    # ── 6. next_action_reasoning ──
    # "what will X want to do next", "what does X need to do", "what will X do next"
    if re.search(r"\bwant to do next\b", q):
        return "next_action_reasoning", "Want-to-do-next -> next_action_reasoning"
    if re.search(r"\b(need to do|going to do|have to do)\b", q):
        return "next_action_reasoning", "Need/going-to-do -> next_action_reasoning"
    if re.search(r"\bwhat (does|will|would) .{1,30} (do|say|try)\b", q):
        return "next_action_reasoning", "What-will-X-do -> next_action_reasoning"
    if re.search(r"\bwhat will\b", q):
        return "next_action_reasoning", "What-will generic -> next_action_reasoning"

    # ── 7. planning_reasoning（向后兼容回退） ──
    return "planning_reasoning", "Default -> planning_reasoning"
