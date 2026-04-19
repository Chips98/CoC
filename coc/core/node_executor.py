"""
节点执行器
==========
执行单个 BDP 推理节点的 LLM 调用。
支持 JSON 解析、think 标签清理、重试、输出缓存。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..prompts.node_prompts import build_compact_guide_prompt
from ..utils.text_utils import clean_think_tags, extract_first_json

logger = logging.getLogger(__name__)

# ── 调试控制 ──
# 通过 config.yaml 的 logging.debug_level 控制（0=关闭, 1=摘要, 2=完整 prompt）
def _get_debug_level() -> int:
    return int(os.environ.get("COC_DEBUG", "0"))


_DIVIDER = "=" * 72
_SUB_DIV = "-" * 60


def _debug_print_node_prompt(node_id: str, messages: List[Dict[str, str]]) -> None:
    if _get_debug_level() < 1:
        return
    print(f"\n{_DIVIDER}")
    print(f"[CoC Node] {node_id}  ── PROMPT")
    print(_SUB_DIV)
    for idx, msg in enumerate(messages):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if _get_debug_level() >= 2:
            print(f"[msg {idx}] role={role}\n{content}\n")
        else:
            # 只显示前 400 字符的摘要
            preview = content[:400].replace("\n", " ")
            print(f"[msg {idx}] role={role} | preview: {preview}{'...' if len(content)>400 else ''}")
    print(_SUB_DIV)


def _debug_print_node_response(node_id: str, raw_text: str, parsed: Dict) -> None:
    if _get_debug_level() < 1:
        return
    print(f"[CoC Node] {node_id}  ── RESPONSE")
    print(_SUB_DIV)
    if _get_debug_level() >= 2:
        print(f"Raw:\n{raw_text}")
    else:
        preview = raw_text[:400].replace("\n", " ")
        print(f"Raw preview: {preview}{'...' if len(raw_text)>400 else ''}")
    print(f"Parsed keys: {list(parsed.keys()) if parsed else '(none)'}")
    print(_DIVIDER + "\n")


@dataclass
class NodeOutput:
    """单个节点的执行结果"""
    node_id: str
    raw_text: str = ""
    parsed: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    retries: int = 0
    prompt_messages: List[Dict[str, str]] = field(default_factory=list)
    error: str = ""


class NodeExecutor:
    """
    节点级 LLM 执行器。
    负责调用 LLM 执行单个推理节点，解析输出，处理重试。
    """

    def __init__(
        self,
        llm_client,
        skills_dir: Path,
        max_retries: int = 3,
        max_words: int = 256,
        temperature: float = 0.1,
        enable_cache: bool = True,
    ):
        # Pipeline is compact-only: one LLM call per chain that produces an
        # integrated thinking guide. The guide is fanned out to every node so
        # downstream consumers (answer_prompt) can render a hybrid layout
        # (BDP role template + sample-specific insight).
        self.llm_client = llm_client
        self.skills_dir = skills_dir
        self.max_retries = max_retries
        self.max_words = max_words
        self.temperature = temperature
        self.enable_cache = enable_cache
        self._cache: Dict[str, NodeOutput] = {}

    def _cache_key(
        self,
        node_id: str,
        context: str,
        question: str,
        options: Dict[str, str],
        prior_outputs: Dict[str, Dict[str, Any]],
        scene_type: str,
    ) -> str:
        """生成缓存键（Bug I：基于完整内容哈希，避免跨样本误命中）"""
        try:
            opt_blob = json.dumps(options, sort_keys=True, ensure_ascii=False)
            prior_blob = json.dumps(prior_outputs, sort_keys=True, ensure_ascii=False)
        except Exception:
            opt_blob = str(options)
            prior_blob = str(prior_outputs)
        raw = "||".join(
            [node_id, scene_type or "", context, question, opt_blob, prior_blob]
        )
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    async def execute_chain(
        self,
        chain: List[str],
        context: str,
        question: str,
        options: Dict[str, str],
        task_input: Optional[Dict[str, Any]] = None,
        scene_type: str = "",
        temperature: Optional[float] = None,
    ) -> Dict[str, NodeOutput]:
        """
        Execute the cognition chain — compact mode only. One LLM call
        produces a single integrated thinking guide that is fanned out
        to every node on the chain.
        """
        return await self._execute_compact_chain(
            chain=chain,
            context=context,
            question=question,
            options=options,
            task_input=task_input,
            scene_type=scene_type,
            temperature=temperature,
        )

    async def _execute_compact_chain(
        self,
        chain: List[str],
        context: str,
        question: str,
        options: Dict[str, str],
        task_input: Optional[Dict[str, Any]] = None,
        scene_type: str = "",
        temperature: Optional[float] = None,
    ) -> Dict[str, NodeOutput]:
        """
        Compact pipeline — one LLM call produces a single integrated
        ~200-token thinking guide for the whole chain. Every node gets a
        copy of the same guide in its `thinking_guide` field; the answer
        stage is responsible for rendering per-node BDP role descriptions
        on top (see `_collect_chain_guides` hybrid layout).
        """
        if not chain:
            return {}

        compact_node_id = "__compact__::" + ",".join(chain)
        ck = None
        if self.enable_cache:
            ck = self._cache_key(
                compact_node_id, context, question, options, {}, scene_type
            )
            if ck in self._cache:
                return self._materialize_compact_outputs(self._cache[ck], chain)

        messages = build_compact_guide_prompt(
            chain=chain,
            context=context,
            question=question,
            options=options,
            skills_dir=self.skills_dir,
            task_input=task_input,
            scene_type=scene_type,
        )

        guide_result = NodeOutput(node_id=compact_node_id, prompt_messages=messages)
        effective_temp = temperature if temperature is not None else self.temperature

        for attempt in range(self.max_retries):
            try:
                raw_text = await self.llm_client.one_chat(
                    messages, temperature=effective_temp,
                )
                raw_text = clean_think_tags(raw_text or "")
                guide_result.raw_text = raw_text
                guide_result.retries = attempt

                parsed = extract_first_json(raw_text) or {}
                # New Node schema emits {"plan": "..."}; fall back to legacy
                # "thinking_guide" key for backward compatibility.
                plan_text = (
                    str(parsed.get("plan", "")).strip()
                    or str(parsed.get("thinking_guide", "")).strip()
                )
                if not plan_text:
                    plan_text = raw_text.strip()
                guide_result.parsed = {
                    "plan": plan_text,
                    "mode": "compact",
                    "chain_nodes": list(chain),
                }
                guide_result.success = bool(plan_text)
                break
            except Exception as e:
                guide_result.error = str(e)
                guide_result.retries = attempt + 1
                logger.warning(f"compact guide attempt {attempt + 1} failed: {e}")

        if self.enable_cache and guide_result.success and ck is not None:
            self._cache[ck] = guide_result

        return self._materialize_compact_outputs(guide_result, chain)

    @staticmethod
    def _materialize_compact_outputs(
        guide_result: "NodeOutput", chain: List[str]
    ) -> Dict[str, "NodeOutput"]:
        """
        Fan one compact-guide LLM result out to per-node NodeOutput entries.
        All nodes share the same `thinking_guide`; differentiation happens
        at the answer-prompt rendering stage via BDP role templates.
        """
        parsed = guide_result.parsed or {}
        plan_text = (
            str(parsed.get("plan", "") or "").strip()
            or str(parsed.get("thinking_guide", "") or "").strip()
        )
        return {
            node_id: NodeOutput(
                node_id=node_id,
                raw_text=guide_result.raw_text,
                parsed={
                    "plan": plan_text,
                    "mode": "compact",
                    "chain_nodes": list(chain),
                },
                success=guide_result.success,
                retries=guide_result.retries,
                prompt_messages=guide_result.prompt_messages,
                error=guide_result.error,
            )
            for node_id in chain
        }

    def clear_cache(self) -> None:
        """清空输出缓存"""
        self._cache.clear()

    def cache_size(self) -> int:
        """返回缓存大小"""
        return len(self._cache)
