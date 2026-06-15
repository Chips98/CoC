"""
CoC 主推理管线
===============
编排完整的推理流程：
route → memory_retrieve → build_priors → mcts_search → execute_chain → generate_answer → compute_reward → update → deposit
"""
from __future__ import annotations

import logging
import os
import shutil
import time
from datetime import datetime
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from .answer_generator import AnswerGenerator
from .bdp_tree import ALL_NODES, node_display_name, validate_chain
from .mcts_search import SearchConfig, SearchState, format_search_log, search_cognition_chain
from .memory_prior import build_memory_prior
from .node_executor import NodeExecutor
from .node_value import NodeStats
from .reward import compute_final_reward, compute_pseudo_reward
from .router import RouteResult, route_scene
from .theory_prior import build_theory_prior

logger = logging.getLogger(__name__)

def _get_debug_level() -> int:
    return int(os.environ.get("COC_DEBUG", "0"))


_DIVIDER = "=" * 72


def _debug_engine(msg: str) -> None:
    if _get_debug_level() >= 1:
        print(f"[CoC Engine] {msg}")


def load_config(config_path: Path) -> Dict[str, Any]:
    """加载 YAML 配置文件，并将 logging.debug_level 同步到环境变量"""
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    debug_level = cfg.get("logging", {}).get("debug_level", 0)
    os.environ["COC_DEBUG"] = str(int(debug_level))
    return cfg


_VALID_BENCHMARKS = {"socialiqa", "social_iqa", "sotopia", "tombench", "simpletom", "simple_tom"}


def _normalize_benchmark(name: str) -> str:
    """把 benchmark 名字归一到标准子目录名"""
    name = (name or "").strip().lower().replace("-", "_")
    mapping = {
        "social_iqa": "socialiqa",
        "simple_tom": "simpletom",
    }
    return mapping.get(name, name) if name else "default"


def resolve_runtime_dir(package_root: Path) -> Path:
    """
    解析运行时目录。
    结构：data/runtime/{benchmark}/{benchmark}_{run_id}/{node_stats.json, memory.jsonl}

    环境变量：
      COC_BENCHMARK  — 指定当前基线名（socialiqa / sotopia / tombench / simpletom）。
                        未设置时回退到 "default"。
      COC_RUN_ID     — 指定本次运行 ID（通常是时间戳）。未设置时自动生成。
      COC_INHERIT_FROM_LATEST — 可选。若设置为 "1"，新建 run 目录会从同 benchmark 下
                                  最近一次 run 复制 node_stats.json / memory.jsonl 作为暖启动。
    """
    benchmark = _normalize_benchmark(os.environ.get("COC_BENCHMARK", "default"))
    run_id = os.environ.get("COC_RUN_ID", "").strip()
    if not run_id:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.environ["COC_RUN_ID"] = run_id  # 让同一 Python 进程内多次实例化共享同一 run

    benchmark_root = package_root / "data" / "runtime" / benchmark
    current_dir = benchmark_root / f"{benchmark}_{run_id}"
    current_dir.mkdir(parents=True, exist_ok=True)

    # 可选：暖启动复制最近一次同基线的 runtime
    if os.environ.get("COC_INHERIT_FROM_LATEST", "0") == "1":
        try:
            existing = [
                p for p in benchmark_root.iterdir()
                if p.is_dir() and p != current_dir
            ]
            existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            if existing:
                prev = existing[0]
                for fname in ("node_stats.json", "memory.jsonl"):
                    src = prev / fname
                    dst = current_dir / fname
                    if src.exists() and not dst.exists():
                        shutil.copy2(src, dst)
                logger.info(f"Runtime warm-start from {prev.name}")
        except Exception as e:
            logger.warning(f"Runtime warm-start failed: {e}")

    return current_dir


class CoCEngine:
    """
    CoC 主推理引擎。
    将 BDP 推理树 + MCTS 搜索 + 节点执行 + 答案生成 + 反馈更新 编排为完整管线。
    """

    def __init__(self, llm_client, config_path: Optional[Path] = None):
        # 加载配置
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent.parent / "configs" / "default.yaml"
        self.cfg = load_config(config_path)
        self.llm_client = llm_client

        # 路径
        package_root = Path(__file__).resolve().parent.parent
        self.skills_dir = package_root / "skills"
        runtime_dir = resolve_runtime_dir(package_root)
        self.runtime_dir = runtime_dir
        self.node_stats_path = runtime_dir / "node_stats.json"
        self.memory_path = runtime_dir / "memory.jsonl"
        _debug_engine(f"runtime_dir = {runtime_dir}")
        logger.info(f"CoC runtime directory: {runtime_dir}")

        # 初始化组件
        mcts_cfg = self.cfg.get("mcts", {})
        ablation = self.cfg.get("ablation", {})
        answer_cfg = self.cfg.get("answer", {})
        llm_cfg = self.cfg.get("llm", {})
        # Pipeline is compact-only: one LLM call per chain produces a shared
        # thinking guide; MCTS is always on; heuristic rule-based overrides
        # are removed. Refinement is opt-in via `verification.enable_*`.

        self.node_stats = NodeStats(
            initial_q=self.cfg.get("node_value", {}).get("initial_q", 0.5),
            alpha=self.cfg.get("node_value", {}).get("alpha", 0.2),
            soft_prune_threshold=self.cfg.get("node_value", {}).get("soft_prune_threshold", 0.25),
            min_visits_for_prune=self.cfg.get("node_value", {}).get("min_visits_for_prune", 5),
        )
        # 加载持久化的 Q/N 值
        self.node_stats.load(self.node_stats_path)

        # 消融：random_rollout 强制覆盖 rollout_strategy
        _rollout_strategy = mcts_cfg.get("rollout_strategy", "greedy")
        if ablation.get("random_rollout", False):
            _rollout_strategy = "random"

        self.search_config = SearchConfig(
            max_depth=self.cfg.get("bdp_tree", {}).get("max_depth", 3),
            num_simulations=mcts_cfg.get("num_simulations", 3),
            lambda_explore=mcts_cfg.get("lambda_explore", 0.4),
            mu_theory=mcts_cfg.get("mu_theory", 0.6),
            nu_memory=mcts_cfg.get("nu_memory", 0.4),
            confidence_threshold=mcts_cfg.get("confidence_threshold", 0.85),
            progressive_widening_k=mcts_cfg.get("progressive_widening_k", 1.0),
            rollout_strategy=_rollout_strategy,
            no_theory_prior=ablation.get("no_theory_prior", False),
            no_value_update=ablation.get("no_value_update", False),
            no_tree_search=ablation.get("no_tree_search", False),
            no_memory_prior=ablation.get("no_memory_prior", False),
            no_progressive_widening=ablation.get("no_progressive_widening", False),
            no_soft_prune=ablation.get("no_soft_prune", False),
            freeze_q_during_eval=bool(mcts_cfg.get("freeze_q_during_eval", False)),
        )

        self.node_executor = NodeExecutor(
            llm_client=llm_client,
            skills_dir=self.skills_dir,
            max_retries=answer_cfg.get("max_retries", 3),
            max_words=answer_cfg.get("node_output_max_words", 256),
            temperature=llm_cfg.get("temperature", 0.1),
        )

        self.answer_generator = AnswerGenerator(
            llm_client=llm_client,
            temperature=0.0,
        )

        # 记忆存储（延迟导入避免循环）
        from ..storage.memory_store import MemoryStore
        self.memory_store = MemoryStore(
            path=self.memory_path,
            capacity=self.cfg.get("memory", {}).get("short_term_capacity", 1000),
        )

        self.routing_mode = self.cfg.get("routing", {}).get("mode", "rule")
        self.memory_enabled = self.cfg.get("memory", {}).get("enable", True) and not ablation.get("no_memory", False)
        self.freeze_q_during_eval = bool(mcts_cfg.get("freeze_q_during_eval", False))
        # Single refinement gate — see Stage 5 in run(). All sub-keys default to False.
        self.verification_cfg = self.cfg.get("verification", {}) or {}

    async def run(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整推理管线。

        参数:
            task_input: 规范化后的任务输入

        返回:
            完整结果字典
        """
        t0 = time.time()

        # Mark sample boundary in optional LLM trace (env var COC_TRACE_PATH).
        if os.environ.get("COC_TRACE_PATH"):
            meta_id = task_input.get("meta", {}).get("sample_id", "")
            q_preview = str(task_input.get("question", ""))[:60].replace("\n", " ")
            marker = f"{task_input.get('task_name','')}::{meta_id}::{q_preview}"
            os.environ["COC_TRACE_MARKER"] = marker
            try:
                with open(os.environ["COC_TRACE_PATH"], "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'#'*78}\n# SAMPLE BEGIN :: {marker}\n{'#'*78}\n")
            except Exception:
                pass

        # ── 1. 路由：获取 scene_type ──
        route_result = route_scene(task_input, mode=self.routing_mode)
        scene_type = route_result.scene_type

        # D2 消融：关闭场景路由 → 所有样本使用同一默认场景（统一理论先验），
        # 以隔离"场景条件化先验 vs 单一通用先验"这一设计点。
        if self.cfg.get("ablation", {}).get("no_scene_routing", False):
            scene_type = "belief_reasoning"

        context = str(task_input.get("context", ""))
        question = str(task_input.get("question", ""))
        options = task_input.get("options", {})
        language = str(task_input.get("language", "en"))
        task_name = str(task_input.get("task_name", ""))
        meta = task_input.get("meta", {})
        correct_answer = str(meta.get("reference_answer", "")).strip() or None

        _debug_engine(
            f"task={task_name}  scene={scene_type}  route={route_result.route_reason[:80] if route_result.route_reason else '?'}"
        )

        # ── 2. 构建先验（按 benchmark 加载对应 JSON 权重）──
        theory_prior = build_theory_prior(scene_type, list(ALL_NODES), benchmark=task_name)

        # 记忆先验
        memory_prior: Dict[str, float] = {}
        if self.memory_enabled and not self.search_config.no_memory_prior:
            retrieved = self.memory_store.retrieve_by_scene(
                scene_type,
                top_k=self.cfg.get("memory", {}).get("retrieval_top_k", 3),
                task_name=task_name,
            )
            memory_prior = build_memory_prior(retrieved)

        # ── 3. 自适应认知链搜索 ──
        # 认知链深度由任务复杂度自适应决定：
        #   SocialIQA: 2-3 步短链（简单 QA 不需要深度 BDP 推理）
        #   TomBench:  4-5 步长链（充分利用 BDP 因果推理链）
        #   Sotopia:   完整 BDP 链（多轮对话需要感知→信念→意图→行动完整链路）
        from dataclasses import replace as _dc_replace
        adaptive_cfg = self.cfg.get("adaptive_chain", {}).get(task_name, {})

        # Per-benchmark_task override (e.g., tombench_false_belief_task).
        # Lets us specialize the chain for weak ToMBench subtasks (FBT, FRT,
        # ...) without touching strong ones. The composite key is built from
        # the normalized benchmark_task: lower-case, spaces → "_", hyphens
        # preserved → "faux-pas recognition test" becomes
        # "tombench_faux-pas_recognition_test".
        benchmark_task_raw = (route_result.benchmark_task or "").strip().lower()
        if benchmark_task_raw:
            bt_key = benchmark_task_raw.replace(" ", "_")
            composite_key = f"{task_name}_{bt_key}"
            override = self.cfg.get("adaptive_chain", {}).get(composite_key) or {}
            if override:
                adaptive_cfg = {**adaptive_cfg, **override}  # subtask wins

        effective_config = _dc_replace(
            self.search_config,
            max_depth=adaptive_cfg.get("max_depth", self.search_config.max_depth),
            num_simulations=adaptive_cfg.get("num_simulations", self.search_config.num_simulations),
        )
        _debug_engine(
            f"Adaptive chain: task={task_name} max_depth={effective_config.max_depth} "
            f"sims={effective_config.num_simulations} no_search={effective_config.no_tree_search}"
        )

        search_state = SearchState(
            scene_type=scene_type,
            node_stats=self.node_stats,
            theory_prior=theory_prior,
            memory_prior=memory_prior,
        )
        chain, search_meta = search_cognition_chain(search_state, effective_config)

        _debug_engine(f"Selected chain: {' -> '.join(chain)}")

        # ── 自适应 temperature ──
        node_temperature = adaptive_cfg.get("temperature", self.node_executor.temperature)
        answer_temperature = adaptive_cfg.get("temperature", self.answer_generator.temperature)

        # ── 4. 执行链上节点 ──
        node_results = await self.node_executor.execute_chain(
            chain=chain,
            context=context,
            question=question,
            options=options,
            task_input=task_input,
            scene_type=scene_type,
            temperature=node_temperature,
        )

        # 提取结构化输出
        node_outputs_parsed = {
            nid: nr.parsed for nid, nr in node_results.items() if nr.success
        }

        # ── 5. 生成答案 ──
        answer_result = await self.answer_generator.generate(
            context=context,
            question=question,
            options=options,
            chain=chain,
            node_outputs=node_outputs_parsed,
            task_name=task_name,
            language=language,
            task_input=task_input,
            scene_type=scene_type,
            temperature=answer_temperature,
        )

        predicted = answer_result.get("answer", "")
        calibrated = False  # kept in result dict for backward compat; always False now.

        _debug_engine(
            f"Answer: final={predicted!r}  guided={answer_result.get('guided_answer','?')!r}"
        )

        # ── 5. Verification / Refinement ──
        # Single refinement gate, controlled exclusively by the `verification`
        # config block. All keys default to False — no silent refinement pass.
        # Multiple-choice benchmarks use `verify_answer` (blind-elimination).
        # Dialogue tasks (Sotopia) use `optimize_sotopia_response`.
        _VERIFY_KEY_MAP = {
            "socialiqa": "enable_socialiqa",
            "social_iqa": "enable_socialiqa",
            "tombench": "enable_tombench",
            "simpletom": "enable_tombench",
            "simple_tom": "enable_tombench",
        }
        verified = False
        is_dialogue = task_name in ("sotopia", "dialogue")
        if is_dialogue and self.verification_cfg.get("enable_sotopia", False):
            optimized = await self.answer_generator.optimize_sotopia_response(
                context=context,
                first_response=predicted,
                task_input=task_input,
                language=language,
            )
            if optimized and optimized != predicted:
                _debug_engine(f"Sotopia optimize: response updated")
                predicted = optimized
                verified = True
                answer_result["answer"] = predicted
        elif options and predicted:
            verify_key = _VERIFY_KEY_MAP.get(task_name.lower())
            if verify_key and self.verification_cfg.get(verify_key, False):
                verified_answer = await self.answer_generator.verify_answer(
                    context=context,
                    question=question,
                    options=options,
                    first_answer=predicted,
                    first_reasoning=answer_result.get("reasoning", ""),
                    task_name=task_name,
                    task_input=task_input,
                    scene_type=scene_type,
                    language=language,
                )
                if verified_answer and verified_answer != predicted:
                    _debug_engine(f"Verification: {predicted} → {verified_answer}")
                    predicted = verified_answer
                    verified = True
                    answer_result["answer"] = predicted

        # ── 6. 计算奖励 ──
        # In compact mode all chain nodes share the same thinking_guide, so
        # coherence across nodes is tautologically 1.0 — zero its weight and
        # split the mass between fit & convergence.
        w_coh = 0.0
        w_fit = self.cfg.get("reward", {}).get("w_fit_compact", 0.5)
        w_conv = self.cfg.get("reward", {}).get("w_convergence_compact", 0.5)
        pseudo_reward = compute_pseudo_reward(
            chain=chain,
            node_outputs=node_outputs_parsed,
            question=question,
            options=options,
            w_coherence=w_coh,
            w_fit=w_fit,
            w_convergence=w_conv,
        )
        final_reward = compute_final_reward(predicted, correct_answer, pseudo_reward)

        # ── 7. 回传更新 Q/N 值 ──
        # Bug #1 fix: 全局 Q/N 只在这里用 final_reward 更新一次（MCTS 内部不再更新）。
        # Bug #2 fix: freeze_q_during_eval 在此处和 MCTS 内部均生效。
        update_details = {}
        if not self.search_config.no_value_update and not self.freeze_q_during_eval:
            update_details = self.node_stats.update(scene_type, chain, final_reward)
            self.node_stats.save(self.node_stats_path)

        # Bug #1: 记录每个样本的 node update 到 node_updates.jsonl
        sample_id = str(meta.get("sample_id", ""))
        node_update_record = {
            "sample_id": sample_id,
            "task_name": task_name,
            "scene_type": scene_type,
            "chain": chain,
            "final_reward": final_reward,
            "pseudo_reward": pseudo_reward,
            "update_details": update_details,
            "frozen": self.freeze_q_during_eval,
        }
        from ..utils.io_utils import append_jsonl
        node_updates_path = self.runtime_dir / "node_updates.jsonl"
        append_jsonl(node_updates_path, node_update_record)

        # ── 8. 记忆沉淀 ──
        if self.memory_enabled:
            from ..utils.text_utils import md5_short
            self.memory_store.deposit(
                scene_type=scene_type,
                chain=chain,
                reward=final_reward,
                context_digest=md5_short(context),
                question=question[:200],
                predicted=predicted,
                correct=correct_answer,
                task_name=task_name,
            )

        wall_time = round(time.time() - t0, 3)

        # ── 构建返回结果 ──
        result = {
            # 主要输出
            "output": answer_result.get("reasoning", ""),
            "final_response": answer_result.get("raw_text", ""),
            "raw_answer": predicted,
            "answer": predicted,

            # 认知链信息
            "chain": chain,
            "chain_display": [node_display_name(n) for n in chain],
            "chain_valid": validate_chain(chain),

            # 节点输出
            "node_outputs": {
                nid: {
                    "parsed": nr.parsed,
                    "success": nr.success,
                    "retries": nr.retries,
                }
                for nid, nr in node_results.items()
            },

            # 搜索信息
            "search_meta": search_meta,

            # 路由信息
            "route": route_result.to_dict(),

            # 奖励信息
            "pseudo_reward": pseudo_reward,
            "final_reward": final_reward,

            # Q 值更新
            "value_updates": update_details,
            "node_stats_snapshot": self.node_stats.snapshot(scene_type),

            # 答案生成信息
            "recovery_method": answer_result.get("recovery_method", ""),
            "calibrated": answer_result.get("calibrated", False),
            "verified": verified,
            "conflict_detected": answer_result.get("conflict_detected", False),
            "guided_answer": answer_result.get("guided_answer", ""),
            "counterfactual_answer": answer_result.get("counterfactual_answer", ""),
            "first_pass_json": answer_result.get("first_pass_json", {}),
            "verification_json": answer_result.get("verification_json", {}),

            # 元信息
            "meta": {
                "scene_type": scene_type,
                "task_name": task_name,
                "wall_time": wall_time,
                "chain_length": len(chain),
                "reasoning_mode": "compact",
                "memory_cases_count": self.memory_store.count(),
                "cache_size": self.node_executor.cache_size(),
            },
        }

        return result

    async def close(self) -> None:
        """清理资源"""
        self.node_stats.save(self.node_stats_path)
