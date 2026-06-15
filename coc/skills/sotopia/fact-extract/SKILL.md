---
name: fact-extract
description: Use at the start of a Sotopia interaction or when a partner's turn introduces new concrete facts — extract the key scenario constraints, role facts, and goal-relevant details that will anchor all subsequent reasoning.
---

# fact-extract

## Skill Kind

- cognition-node

## Node Role

- Extract the most important concrete facts from the Sotopia scenario background.
- Pull out role-specific constraints, relationship context, and goal-relevant details.
- Build a compact factual foundation for downstream reasoning nodes.

## When To Use

- Use on the first turn of an interaction to ground reasoning in scenario facts.
- Use after the partner reveals new facts (price, deadline, relationship history, constraint).
- Use when the background text is dense and downstream nodes need a condensed reference.

## Required Inputs

- Scenario background / context
- Agent profile (name, role, relationship to partner)
- Partner's latest statement (if any)

## Output Contract

- Core scenario facts (setting, relationship, stakes)
- Agent's role-specific constraints (budget, deadline, social obligation)
- Partner's inferred constraints (from background or their statement)
- Goal alignment: what facts support vs. oppose achieving the goal this turn

## Methodology

- Read background once; identify: who, what, where, stakes, any explicit constraints.
- Separate facts that are public (both parties know) from agent-private (only in agent's background).
- Highlight exactly 2-3 facts most directly relevant to the current turn decision.
- Do not invent facts not supported by the background or partner's statements.
- If the partner stated a constraint (price limit, time limit, personal rule), mark it as confirmed partner-fact.

## Pitfalls

- Do not conflate scenario background with what the agent should say — this is information extraction, not response writing.
- Do not include emotional interpretation here; leave that to `emotion`.
- Do not over-elaborate; the output should be compact and precise.
- Do not copy-paste the entire background; summarize the key load-bearing facts.

## Switch Rules

- If extracted facts reveal a belief gap, add `belief-state`.
- If facts include the partner's emotional signals, add `emotion`.
- If facts directly inform the turn tactic, pass to `intent-strategy`.
