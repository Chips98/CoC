"""
Final answer generation with dual-pass reasoning and conflict-triggered verification.
"""
from __future__ import annotations

import logging
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from ..prompts.node_prompts import build_answer_prompt, build_calibration_prompt
from ..utils.text_utils import (
    clean_think_tags,
    extract_choice_label,
    extract_first_json,
    recover_answer_by_last_line,
    recover_answer_by_option_text,
)

logger = logging.getLogger(__name__)

# ── 调试控制（通过 config.yaml 的 logging.debug_level 控制）──
def _get_debug_level() -> int:
    return int(os.environ.get("COC_DEBUG", "0"))


_DIVIDER = "=" * 72
_SUB_DIV = "-" * 60


def _debug_print_answer_prompt(messages: List[Dict[str, str]], stage: str = "Answer") -> None:
    if _get_debug_level() < 1:
        return
    print(f"\n{_DIVIDER}")
    print(f"[CoC {stage}]  ── PROMPT")
    print(_SUB_DIV)
    for idx, msg in enumerate(messages):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if _get_debug_level() >= 2:
            print(f"[msg {idx}] role={role}\n{content}\n")
        else:
            preview = content[:500].replace("\n", " ")
            print(f"[msg {idx}] role={role} | preview: {preview}{'...' if len(content)>500 else ''}")
    print(_SUB_DIV)


def _debug_print_answer_response(raw_text: str, parsed: Dict, stage: str = "Answer") -> None:
    if _get_debug_level() < 1:
        return
    print(f"[CoC {stage}]  ── RESPONSE")
    print(_SUB_DIV)
    if _get_debug_level() >= 2:
        print(f"Raw:\n{raw_text}")
    else:
        preview = raw_text[:500].replace("\n", " ")
        print(f"Raw preview: {preview}{'...' if len(raw_text)>500 else ''}")
    print(f"Parsed: guided={parsed.get('guided_answer','?')}  cf={parsed.get('counterfactual_answer','?')}  final={parsed.get('final_answer', parsed.get('reply','?'))}")
    print(_DIVIDER + "\n")


class AnswerGenerator:
    """Generate final answer from cognition-chain guides."""

    def __init__(
        self,
        llm_client,
        temperature: float = 0.0,
    ):
        self.llm_client = llm_client
        self.temperature = temperature

    async def generate(
        self,
        context: str,
        question: str,
        options: Dict[str, str],
        chain: List[str],
        node_outputs: Dict[str, Dict[str, Any]],
        task_name: str = "",
        language: str = "en",
        task_input: Optional[Dict[str, Any]] = None,
        scene_type: str = "",
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Return:
            {
              "answer": "A",
              "reasoning": "...",
              "raw_text": "...",
              "recovery_method": "...",
              "calibrated": bool,
              "answer_prompt": [...],
              "conflict_detected": bool,
              "guided_answer": "A",
              "counterfactual_answer": "B",
              "first_pass_json": {...},
              "verification_json": {...},
            }
        """
        # Bug #8: 反事实推理和校准已完全移除，只做单次推理
        task_type = str((task_input or {}).get("task_type", "") or "").lower()
        is_dialogue_task = "dialogue" in task_type or str(task_name or "").strip().lower() in {"sotopia", "dialogue"}

        messages = build_answer_prompt(
            context=context,
            question=question,
            options=options,
            chain=chain,
            node_outputs=node_outputs,
            task_name=task_name,
            language=language,
            task_input=task_input,
            scene_type=scene_type,
            enable_counterfactual=False,
        )
        _debug_print_answer_prompt(messages, stage="AnswerGen")

        effective_temp = temperature if temperature is not None else self.temperature
        raw_text = await self.llm_client.one_chat(messages, temperature=effective_temp)
        raw_text = clean_think_tags(raw_text or "")
        parsed = extract_first_json(raw_text) or {}
        _debug_print_answer_response(raw_text, parsed, stage="AnswerGen")

        if is_dialogue_task:
            reply_text = (
                str(parsed.get("reply", "")).strip()
                or str(parsed.get("final_answer", "")).strip()
                or str(parsed.get("answer", "")).strip()
                or str(parsed.get("guided_answer", "")).strip()
            )
            if not reply_text:
                reply_text = raw_text.strip()
            reply_text = self.clean_dialogue_reply(reply_text)

            return {
                "answer": reply_text,
                "reasoning": raw_text,
                "raw_text": raw_text,
                "recovery_method": "dialogue_reply",
                "calibrated": False,
                "answer_prompt": messages,
                "conflict_detected": False,
                "guided_answer": reply_text,
                "counterfactual_answer": "",
                "first_pass_json": parsed,
                "verification_json": {},
            }

        # Multiple-choice: prefer final_answer, then answer.
        final_answer_text = (
            str(parsed.get("final_answer", "")).strip()
            or str(parsed.get("answer", "")).strip()
        )
        guided_answer_text = str(parsed.get("guided_answer", "")).strip()

        final_answer, recovery_method = self._resolve_answer(final_answer_text, raw_text, options)
        guided_answer, _ = self._resolve_answer(guided_answer_text, guided_answer_text, options)

        # Last-resort fallback: if label extraction completely failed, pick
        # option A to avoid empty answer (marked so downstream sees the fail).
        if not final_answer and options:
            final_answer = list(options.keys())[0]
            recovery_method = "fallback"

        return {
            "answer": final_answer,
            "reasoning": raw_text,
            "raw_text": raw_text,
            "recovery_method": recovery_method,
            "calibrated": False,
            "answer_prompt": messages,
            "conflict_detected": False,
            "guided_answer": guided_answer,
            "counterfactual_answer": "",
            "first_pass_json": parsed,
            "verification_json": {},
        }

    @staticmethod
    def _is_repetitive(reply: str, previous_messages: List[str], threshold: float = 0.55) -> bool:
        """Check if reply is too similar to any previous message using word overlap."""
        if not reply or not previous_messages:
            return False
        # Normalize: lowercase, strip punctuation, split
        import string
        def _normalize(text: str) -> set:
            text = text.lower().translate(str.maketrans("", "", string.punctuation))
            return set(text.split())
        reply_words = _normalize(reply)
        if len(reply_words) < 4:
            return False
        for prev in previous_messages:
            prev_words = _normalize(prev)
            if len(prev_words) < 4:
                continue
            overlap = len(reply_words & prev_words)
            similarity = overlap / max(len(reply_words), len(prev_words))
            if similarity > threshold:
                return True
        return False

    @staticmethod
    def clean_dialogue_reply(text: str) -> str:
        if not text:
            return ""

        cleaned = clean_think_tags(text or "").strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        json_obj = extract_first_json(cleaned)
        if isinstance(json_obj, dict):
            for key in ("reply", "utterance", "final_answer", "answer", "guided_answer", "speak"):
                value = json_obj.get(key)
                if isinstance(value, str) and value.strip():
                    cleaned = value.strip()
                    break
            else:
                try:
                    cleaned = json.dumps(json_obj, ensure_ascii=False)
                except Exception:
                    pass
        else:
            # ── BUG A FIX: regex-extract "reply" from truncated JSON ──────────
            # When the LLM output is cut-off (missing closing "}"), extract_first_json
            # returns None. We must run the regex NOW, before strip('"') removes the
            # closing quote of the reply value and makes the regex unmatchable.
            _reply_match = re.search(
                r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)"',
                cleaned,
                re.DOTALL,
            )
            if _reply_match:
                _extracted = _reply_match.group(1).strip()
                # Accept only if it looks like real dialogue (not a nested JSON blob)
                if _extracted and '"guided_thought"' not in _extracted and len(_extracted) > 3:
                    return _extracted

        cleaned = cleaned.strip()
        # Only strip surrounding quotes when the ENTIRE string is wrapped in them
        # (e.g. the LLM replied with "Sure, let's go!" — strip to Sure, let's go!)
        # Do NOT use blind .strip('"') which also eats interior quotes like:
        #   Alex should say "hi"  →  Alex should say "hi   (trailing " gone → regex breaks)
        if len(cleaned) > 2 and cleaned[0] == '"' and cleaned[-1] == '"':
            cleaned = cleaned[1:-1].strip()
        elif len(cleaned) > 2 and cleaned[0] == "'" and cleaned[-1] == "'":
            cleaned = cleaned[1:-1].strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return ""

        lowered = cleaned.lower()
        if lowered.startswith("{") and lowered.endswith("}"):
            return ""
        if lowered in {"a", "b", "c", "d"}:
            return ""
        if "guided_thought" in lowered or "counterfactual" in lowered:
            return ""

        # Instruction leakage detection: if the text contains meta-instructions
        # (coaching phrases, imperative prompts) instead of natural dialogue, reject it
        _instruction_markers = [
            "do not repeat", "respond to the partner", "pursue a smaller",
            "micro-goal", "change the framing", "pivot to a new angle",
            "acknowledge their concern", "should express", "should acknowledge",
            "the best move is", "strategy shift", "anti-repeat",
            "each turn should", "available actions", "output json",
            "guided_answer", "final_answer", "benchmark rules",
        ]
        if sum(1 for m in _instruction_markers if m in lowered) >= 2:
            # This is leaked instruction text, not dialogue — reject
            return ""

        rewritten = AnswerGenerator._rewrite_instructional_dialogue(cleaned)
        if rewritten:
            return rewritten

        return cleaned

    @staticmethod
    def _rewrite_instructional_dialogue(text: str) -> str:
        """
        Convert instructional / coaching text into a first-person utterance.

        Handles patterns like:
          "Alex should say 'I understand...'"  → "I understand..."
          "Alex should offer $120"             → "I can offer $120."
          "Alex should ask Bob to split"       → "Could we split?"
          "Alex should acknowledge X"          → "I understand X."
          "Alex should express X"              → "I'd like to express X."
          "Alex should tell Bob that X"        → "X"  (extract content)
          "Alex should mention X"              → "Just to mention -- X."

        Returns "" only if the text genuinely cannot be salvaged.
        """
        match = re.match(
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+should\s+(.+)$",
            text.strip(),
            re.DOTALL,
        )
        if not match:
            return ""

        instruction = match.group(2).strip().rstrip(".")
        instruction = re.sub(
            r"^(directly|politely|gently|calmly|simply|clearly)\s+",
            "",
            instruction,
            flags=re.IGNORECASE,
        )

        lowered = instruction.lower()

        # ── Price / offer with dollar amount ──
        if re.search(r"\$\s*\d+", instruction) or ("offer" in lowered and re.search(r"\d+", instruction)):
            price_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)", instruction)
            if price_match:
                price = price_match.group(1)
                if "offer" in lowered or "price" in lowered:
                    return f"I can do ${price} -- would that work for you?"
                if "want" in lowered or "looking" in lowered:
                    return f"I was hoping for around ${price}. Does that fit your range?"

        # ── ask [Person] to [action] ──
        ask_match = re.search(
            r"ask\s+(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)?\s*to\s+(.+)$",
            instruction, flags=re.IGNORECASE
        )
        if ask_match:
            action = ask_match.group(1).strip()
            action = re.sub(r",?\s*emphasizing.*$", "", action, flags=re.IGNORECASE).strip()
            action = re.sub(r",?\s*while\s+.+$", "", action, flags=re.IGNORECASE).strip()
            if action:
                return f"Could you {action}?"

        # ── say "quoted text" or say: text ──
        say_match = re.search(r'say\s+["\u201c](.+?)["\u201d]', instruction, flags=re.IGNORECASE)
        if say_match:
            return say_match.group(1).strip()
        say_colon = re.search(r"say:\s*(.+)$", instruction, flags=re.IGNORECASE)
        if say_colon:
            return say_colon.group(1).strip()

        # ── tell [Person] that [content] ──
        tell_match = re.search(
            r"tell\s+(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)?\s*that\s+(.+)$",
            instruction, flags=re.IGNORECASE
        )
        if tell_match:
            content = tell_match.group(1).strip().rstrip(".")
            if content:
                return f"{content[0].upper()}{content[1:]}."

        # ── acknowledge / admit ──
        if re.match(r"^acknowledge\b", lowered):
            content = re.sub(r"^acknowledge\s+(that\s+)?", "", instruction, flags=re.IGNORECASE).strip().rstrip(".")
            if content:
                return f"I understand -- {content[0].lower()}{content[1:]}."

        # ── apologize / sorry ──
        if re.match(r"^(apologize|say sorry)\b", lowered):
            reason = re.sub(r"^(apologize|say sorry)\s+(for\s+)?", "", instruction, flags=re.IGNORECASE).strip().rstrip(".")
            if reason:
                return f"I'm sorry about {reason[0].lower()}{reason[1:]}."
            return "I'm sorry about that."

        # ── express [something] ──
        if re.match(r"^express\b", lowered):
            content = re.sub(r"^express\s+", "", instruction, flags=re.IGNORECASE).strip().rstrip(".")
            if content:
                return f"I want to be clear -- {content[0].lower()}{content[1:]}."

        # ── suggest / propose ──
        if re.match(r"^(suggest|propose)\b", lowered):
            content = re.sub(r"^(suggest|propose)\s+(that\s+)?", "", instruction, flags=re.IGNORECASE).strip().rstrip(".")
            if content:
                return f"How about {content[0].lower()}{content[1:]}?"

        # ── explain ──
        if re.match(r"^explain\b", lowered):
            content = re.sub(r"^explain\s+(that\s+)?", "", instruction, flags=re.IGNORECASE).strip().rstrip(".")
            if content:
                return f"Let me explain -- {content[0].lower()}{content[1:]}."

        # ── mention ──
        if re.match(r"^mention\b", lowered):
            content = re.sub(r"^mention\s+(that\s+)?", "", instruction, flags=re.IGNORECASE).strip().rstrip(".")
            if content:
                return f"I just wanted to mention that {content[0].lower()}{content[1:]}."

        # ── make a counteroffer ──
        instruction = re.sub(r",?\s*emphasizing.*$", "", instruction, flags=re.IGNORECASE).strip()
        instruction = re.sub(r",?\s*while\s+.+$", "", instruction, flags=re.IGNORECASE).strip()
        if instruction.lower().startswith("make a counteroffer"):
            return "I am interested, but I need a lower price to make this work for me."

        # ── Generic first-person conversion for remaining verb patterns ──
        # If instruction starts with a plain verb, convert to first-person
        first_word = instruction.split()[0].lower() if instruction.split() else ""
        _first_person_map = {
            "decline": "I'll have to decline that one.",
            "refuse": "I'm afraid I can't agree to that.",
            "accept": "That works for me -- let's go with that.",
            "agree": "I agree with that.",
            "disagree": "I'm not sure I agree on that point.",
            "negotiate": "Can we work on the terms a bit more?",
            "leave": "",  # leave action, let adapter handle
            "stay": "I think I'll stay a bit longer.",
        }
        if first_word in _first_person_map:
            return _first_person_map[first_word]

        # ── Fallback: strip "should" and return the instruction as-is ──
        # Better to return the instruction text (may sound slightly off) than empty string
        if len(instruction) > 10:
            # Capitalize if not already
            return f"{instruction[0].upper()}{instruction[1:]}."

        return ""

    def _resolve_answer(
        self,
        primary_text: str,
        fallback_text: str,
        options: Dict[str, str],
    ) -> Tuple[str, str]:
        """
        Resolve answer label/text from preferred field, then fallback body text.
        """
        if options:
            if primary_text:
                answer, method = self._extract_answer(primary_text, options)
                if answer:
                    return answer, f"field_{method}"
            return self._extract_answer(fallback_text, options)
        return (primary_text or fallback_text or "").strip(), "direct_text"

    def _extract_answer(
        self,
        text: str,
        options: Dict[str, str],
    ) -> Tuple[str, str]:
        if not options:
            return text.strip(), "direct"

        valid_labels = list(options.keys())
        direct = extract_choice_label(text, valid_labels)
        if direct:
            return direct, "direct_extract"

        last_line = recover_answer_by_last_line(text, options)
        if last_line:
            return last_line, "last_line_match"

        full_text = recover_answer_by_option_text(text, options)
        if full_text:
            return full_text, "full_text_match"

        return "", "none"

    async def calibrate_answer(
        self,
        context: str,
        question: str,
        options: Dict[str, str],
        first_answer: str,
        first_reasoning: str,
        task_input: Optional[Dict[str, Any]] = None,
        scene_type: str = "",
        language: str = "en",
    ) -> Optional[str]:
        """
        V1 backport: 轻量答案校准。
        从头重读故事，用零温度LLM验证初始答案是否正确。
        不同于旧的counterfactual系统——这是一个独立的验证步骤。
        """
        if not options or not first_answer:
            return None

        options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
        valid_labels = sorted(options.keys())
        labels_str = "/".join(valid_labels)

        # 收集 benchmark-specific 校准规则
        from ..benchmarks.socialiqa.task_priors import (
            collect_socialiqa_reasoning_rules,
            collect_socialiqa_calibration_examples,
        )
        meta = (task_input or {}).get("meta") or {}
        task_name = str((task_input or {}).get("task_name", "")).strip().lower()

        benchmark_rules = ""
        calibration_examples = ""
        if task_name in ("socialiqa", "social_iqa"):
            rules = collect_socialiqa_reasoning_rules(question)
            examples = collect_socialiqa_calibration_examples(question)
            if rules:
                benchmark_rules = "\n".join(f"- {r}" for r in rules)
            if examples:
                calibration_examples = "\n".join(f"- {e}" for e in examples)

        system_prompt = (
            "You are the final answer calibrator for a social reasoning multiple-choice benchmark. "
            "Choose the best option label using the story, question, options, and benchmark rules. "
            "Treat the assistant draft as fallible evidence, not as ground truth. "
            "If the draft label conflicts with the task details or benchmark rules, ignore the draft label. "
            f"Output only one label ({labels_str}). Do not output any explanation. "
            "no think"
        )

        user_parts = [
            f"Situation:\n{context}\n",
            f"Question:\n{question}\n",
            f"Options:\n{options_text}\n",
        ]
        if benchmark_rules:
            user_parts.append(f"Benchmark rules:\n{benchmark_rules}\n")
        if calibration_examples:
            user_parts.append(f"Calibration examples:\n{calibration_examples}\n")
        user_parts.append(
            f"Assistant draft answer: {first_answer}\n\n"
            "Calibration rules:\n"
            "- Re-read the story and options from scratch.\n"
            "- Follow benchmark rules strictly when present.\n"
            "- Use calibration examples as concrete guidance.\n"
            "- Do not preserve a wrong draft answer.\n"
            f"- Return only one of: {labels_str}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(user_parts)},
        ]

        try:
            raw = await self.llm_client.one_chat(messages, temperature=0.0)
            raw = clean_think_tags(raw or "").strip()
            answer, _ = self._resolve_answer(raw, raw, options)
            return answer if answer else None
        except Exception as e:
            logger.warning(f"Calibration failed: {e}")
            return None

    async def verify_answer(
        self,
        context: str,
        question: str,
        options: Dict[str, str],
        first_answer: str,
        first_reasoning: str,
        task_name: str = "",
        task_input: Optional[Dict[str, Any]] = None,
        scene_type: str = "",
        language: str = "en",
    ) -> Optional[str]:
        """
        Elimination-based blind verification:
        - 不展示第一次的答案（避免锚定偏差）
        - 让 LLM 逐项排除错误选项，给出正确选项的理由，确保自洽
        - TomBench: 追溯心理状态链后逐项排除
        """
        if not options or not first_answer:
            return None

        valid_labels = sorted(options.keys())
        labels_str = "/".join(valid_labels)
        options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))

        is_tombench = task_name in ("tombench", "simpletom", "simple_tom")

        if is_tombench:
            system_prompt = (
                "You are a Theory-of-Mind reasoning expert.\n"
                "Trace each character's mental states step by step.\n"
                "Then eliminate wrong options one by one and pick the best.\n"
                f"End with exactly one label ({labels_str})."
            )
            user_prompt = (
                f"Situation:\n{context}\n\n"
                f"Question:\n{question}\n\n"
                f"Options:\n{options_text}\n\n"
                f"For each option, state whether it fits the story or not and why. "
                f"Eliminate the ones that don't fit. Pick the remaining one.\n"
                f"Answer ({labels_str}):"
            )
        else:  # SocialIQA — elimination reasoning
            system_prompt = (
                "You are a social reasoning expert.\n"
                "Re-read the story carefully. For each option, briefly say why it fits or doesn't fit.\n"
                "Eliminate the wrong options, then pick the best one.\n"
                f"End with exactly one label ({labels_str})."
            )
            user_prompt = (
                f"Situation:\n{context}\n\n"
                f"Question:\n{question}\n\n"
                f"Options:\n{options_text}\n\n"
                f"Evaluate each option against the story. Eliminate wrong ones. Pick the best.\n"
                f"Answer ({labels_str}):"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw = await self.llm_client.one_chat(messages, temperature=0.0)
            raw = clean_think_tags(raw or "").strip()
            _debug_print_answer_response(raw, {}, stage="Verify-eliminate")
            answer, _ = self._resolve_answer(raw, raw, options)
            return answer if answer else None
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            return None

    async def optimize_sotopia_response(
        self,
        context: str,
        first_response: str,
        task_input: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Optional[str]:
        """
        Sotopia 回复维度优化（增强版）：
        对 BEL/REL/KNO/SEC/SOC/FIN/GOAL 逐维度分析第一次回复，
        结合完整对话历史和伙伴最新发言，产出优化版本。
        """
        if not first_response or not first_response.strip():
            return None

        meta = (task_input or {}).get("meta") or {}
        agent_goal = (str(meta.get("goal", "")).strip()
                      or str(meta.get("agent_goal", "")).strip())
        agent_name = str(meta.get("agent_name", "You")).strip()
        partner_name = str(meta.get("partner_name", "the partner")).strip()
        turn_number = int(meta.get("turn_number", 0) or 0)
        current_obs = str(meta.get("current_observation", "")).strip()

        # 构建对话历史
        history = (task_input or {}).get("history") or []
        history_text = ""
        own_recent = []
        if history:
            lines = []
            for h in history[-8:]:
                if isinstance(h, dict):
                    role = h.get("role", "?")
                    content = str(h.get("content", ""))[:250]
                    lines.append(f"[{role}]: {content}")
                    if str(role).lower() == agent_name.lower():
                        own_recent.append(content[:150])
            history_text = "\n".join(lines)

        # Detect negotiation context for FIN-specific guidance
        is_negotiation = any(k in (agent_goal or "").lower() for k in
                            ["target price", "buyer", "seller", "purchase", "price"])

        system_prompt = (
            "You are optimizing a social dialogue response. Evaluate and improve the draft response.\n"
            "Scoring dimensions (how the evaluator actually scores):\n"
            "  BEL[0,10] — naturalness + character consistency. Penalty for being OVERLY POLITE or robotic.\n"
            "  REL[-5,5] — relationship CHANGE: is the relationship better AFTER this exchange? "
            "Requires mutual understanding, not just politeness.\n"
            "  KNO[0,10] — new information GAINED through interaction. Ask questions, acknowledge new facts.\n"
            "  SEC[-10,0] — secret protection: don't leak hidden goals or private constraints.\n"
            "  SOC[-10,0] — social norms: no revenge, threats, or rudeness.\n"
            "  FIN[-5,5] — financial/material outcome of the interaction.\n"
            "  GOAL[0,10] — how much of the character's social goal was achieved.\n\n"
            "Optimization Rules:\n"
            "  1. Natural first-person speech (1-3 sentences). NOT overly polite or formal.\n"
            "  2. MUST directly respond to partner's last message AND advance goal.\n"
            "  3. MUST differ from previous messages. Rewrite completely if similar.\n"
            "  4. NOT coaching text, plans, or stage directions.\n"
            "  5. Keep SEC=0 and SOC=0. Maximize GOAL first, then REL and KNO.\n"
            "  6. For KNO: acknowledge something you LEARNED from the partner, or ask a new question.\n"
            "  7. For REL: find common ground or offer mutual support, not just surface warmth.\n"
        )
        if is_negotiation:
            system_prompt += (
                "  8. NEGOTIATION: Never reveal your target price. Use strategic numbers that leave room to negotiate.\n"
                "  9. A closed deal with moderate concession is BETTER than no deal (FIN=-5 for both if no deal).\n"
                "  10. If stuck for 2+ turns at the same price, make a meaningful concession to close.\n"
            )
        system_prompt += (
            'Output JSON: {"issues": ["..."], "optimized_response": "...", "key_changes": ["..."]}\n'
            "no think"
        )

        user_parts = [f"Background:\n{context}\n"]
        if history_text:
            user_parts.append(f"Conversation so far:\n{history_text}\n")
        if current_obs:
            user_parts.append(f"Partner's latest message: \"{current_obs[:300]}\"\n"
                              "Your reply MUST directly address what they just said.\n")
        if agent_goal:
            user_parts.append(f"Your goal (PRIVATE — do not reveal): {agent_goal[:300]}\n")
        user_parts.append(f"Turn: {turn_number}. You are {agent_name}.\n")
        if own_recent:
            user_parts.append("Your previous messages (MUST NOT repeat or closely paraphrase):")
            for msg in own_recent[-4:]:
                user_parts.append(f'  - "{msg}"')
            user_parts.append("If the draft below is similar to any of the above, you MUST completely rewrite it.\n")
        user_parts.append(f"Draft response to optimize:\n\"{first_response}\"\n")
        user_parts.append(
            "Analyze the draft on all 7 dimensions. Focus especially on:\n"
            "- REL: Does it acknowledge the partner warmly? Add warmth if missing.\n"
            "- KNO: Does it reference specific scenario details? Add relevant context.\n"
            "- GOAL: Does it make concrete progress toward the goal? Make it more actionable.\n"
            "- REPETITION: Is it too similar to previous messages? Rewrite with new approach if so.\n"
            "Produce an optimized_response that fixes issues while sounding natural and in-character."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(user_parts)},
        ]

        try:
            raw = await self.llm_client.one_chat(messages, temperature=0.0)
            raw = clean_think_tags(raw or "").strip()
            parsed = extract_first_json(raw) or {}
            _debug_print_answer_response(raw, parsed, stage="SotopiaOptimize")
            optimized = str(parsed.get("optimized_response", "")).strip()
            if not optimized:
                return None
            return self.clean_dialogue_reply(optimized) or None
        except Exception as e:
            logger.warning(f"Sotopia optimization failed: {e}")
            return None

    async def _calibrate(
        self,
        context: str,
        question: str,
        options: Dict[str, str],
        first_answer: str,
        first_reasoning: str,
        language: str,
        first_pass_json: Optional[Dict[str, Any]] = None,
        task_input: Optional[Dict[str, Any]] = None,
        scene_type: str = "",
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Conflict verification: only called when two-pass answers disagree."""
        try:
            messages = build_calibration_prompt(
                context=context,
                question=question,
                options=options,
                first_answer=first_answer,
                first_reasoning=first_reasoning,
                language=language,
                first_pass_json=first_pass_json,
                task_input=task_input,
                scene_type=scene_type,
            )
            # print("\n=============== Conflict Verification (Prompt) ==============")
            # for idx, message in enumerate(messages):
            #     role = message.get("role", "")
            #     content = message.get("content", "")
            #     print(f"[{idx}] role={role}\n{content}\n")
            # print("=============================================================\n")

            raw = await self.llm_client.one_chat(messages, temperature=0.0)
            raw = clean_think_tags(raw or "")
            # print("\n=============== Conflict Verification (Raw Output) ==========")
            # print(raw)
            # print("=============================================================\n")

            parsed = extract_first_json(raw) or {}
            candidate = str(parsed.get("final_answer", "")).strip()
            answer, _ = self._resolve_answer(candidate, raw, options)
            selected = str(parsed.get("selected_hypothesis", "")).strip().lower()
            if not answer and first_pass_json:
                if selected == "guided":
                    answer, _ = self._resolve_answer(
                        str(first_pass_json.get("guided_answer", "")).strip(),
                        "",
                        options,
                    )
                elif selected == "counterfactual":
                    answer, _ = self._resolve_answer(
                        str(first_pass_json.get("counterfactual_answer", "")).strip(),
                        "",
                        options,
                    )
            return (answer if answer else None), parsed
        except Exception as e:
            logger.warning(f"冲突核查失败: {e}")
            return None, {}

