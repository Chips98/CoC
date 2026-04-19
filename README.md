# CoC — Chain-of-Cognition

Reference implementation for the paper *"CoC: A Chain-of-Cognition Agent
for Social Reasoning"*. CoC is a structured social-reasoning agent that
plans and executes reasoning along a **Belief–Desire–Perception (BDP)**
cognition tree and selects a path with **MCTS**.

This repository is a **clean release**: the overall method, modules, and
control flow are identical to what is reported in the paper, but the
hand-crafted per-benchmark / per-task / per-ability lookup tables that
existed in our research codebase have been **removed**. What remains is
the generic BDP + MCTS pipeline, so results produced here are slightly
lower than, but qualitatively consistent with, the numbers reported in
the paper.

---

## Method at a glance

```
          ┌───────────── Router ─────────────┐
          │ scene_type ∈ {emotion, desire,  │
          │  belief, knowledge, intention,  │
          │  nonliteral, planning, social}  │
          └──────────────┬──────────────────┘
                         │
                ┌────────▼────────┐
                │   BDP  Tree     │   Ctx → 1–3 BDP primitives → Answer
                │ (cognition map) │
                └────────┬────────┘
                         │
   Priors  ──► P_BDP (theory) + P_MEM (memory) + P_TASK (generic)
                         │
                ┌────────▼────────┐
                │   MCTS search   │   pseudo-reward on each simulation
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │ Node executor   │   each chosen node emits a short guide
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │ Answer generator│   dual-pass (guided + counterfactual)
                └─────────────────┘
```

Core modules live under `coc/core/`:

| file | role in the paper |
|------|-------------------|
| `bdp_tree.py` | the BDP cognition graph (edges, legal children, leaves) |
| `router.py` | scene-type routing from (question, context, task_name) |
| `theory_prior.py` | theoretical prior **P_BDP(v \| x)** over BDP nodes |
| `memory_prior.py` | memory-based prior **P_MEM** via embedding retrieval |
| `task_priors.py` | generic task prior (**P_TASK**) hook — no per-task tuning |
| `mcts_search.py` | UCT search over the BDP tree, seeded by the priors |
| `node_executor.py` | per-node guide generation |
| `node_value.py` | value back-propagation |
| `reward.py` | pseudo + final reward |
| `answer_generator.py` | final answer stage (guided + counterfactual) |
| `engine.py` | end-to-end pipeline |

Prompts and benchmark routers live under `coc/prompts/` and
`coc/benchmarks/`.

---

## Install

```bash
git clone https://github.com/Chips98/CoC.git
cd CoC
pip install -r requirements.txt
```

CoC needs two services:

1. **An OpenAI-compatible chat completion endpoint** for the main LLM
   (OpenAI API, vLLM, TGI, llama.cpp server, etc.). Set `llm.api_base`
   and `llm.api_key` in `configs/default.yaml`.
2. **An OpenAI-compatible embedding endpoint** (only used by the
   memory prior). Set `embedding.api_base` / `embedding.model`.

Any OpenAI-compatible server will work; the defaults point to a local
vLLM serving `Qwen3-8B` and `Qwen3-Embedding-4B`.

---

## Quick start — single example

```bash
python examples/single_example.py
```

This runs one ToM-style question through the full BDP + MCTS pipeline
and prints the cognition chain and the final answer.

---

## Reproducing benchmark results

We provide thin eval harnesses for the three benchmarks reported in the
paper. Bring your own splits (we do not ship benchmark data here).

```bash
# ToMBench
python scripts/run_tombench.py  --data /path/to/tombench.jsonl  --out results/tombench

# SocialIQA
python scripts/run_socialiqa.py --data /path/to/socialiqa.jsonl --out results/socialiqa

# Sotopia
python scripts/run_sotopia.py   --data /path/to/sotopia.jsonl   --out results/sotopia
```

Each script writes per-sample JSONL + an aggregate report.

---

## Differences from the research codebase

The research codebase contained ~1,400 lines of hand-crafted priors
indexed by `(benchmark_task, ability, question_type)` — for example:

- 50+ scene-critical rules for ToMBench sub-abilities,
- plan-writing softeners for 5 ToMBench weak tasks,
- per-question calibration examples for SocialIQA,
- per-goal / per-history heuristics for Sotopia bargaining.

All of the above has been **removed** from this release. The clean
repo keeps a single generic prior and an empty interface for people
who want to re-introduce their own priors.

---

## License

MIT — see [LICENSE](LICENSE).
