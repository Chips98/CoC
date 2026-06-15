---
name: constraint-parse
description: Use when a Sotopia turn requires identifying the hard limits and soft preferences that constrain both parties' moves — budget, time, social obligation, relationship rules — before committing to a tactic.
---

# constraint-parse

## Skill Kind

- cognition-node

## Node Role

- Parse the explicit and implicit constraints on this Sotopia interaction.
- Distinguish hard limits (cannot be violated) from soft preferences (can be adjusted with cost).
- Map constraints to identify the feasible solution space for the agent's goal.

## When To Use

- Use at the start of a negotiation, persuasion, or boundary-setting interaction.
- Use when the partner has stated a constraint (price, time, condition) that affects the feasible solution space.
- Use when the agent's goal requires navigating around a known partner restriction.
- Use when deciding what concession is possible without violating the agent's own hard limits.

## Required Inputs

- Agent's goal and private constraints (from background)
- Partner's stated constraints (from their messages)
- Scenario context (transaction, relationship, social obligation)

## Output Contract

- Agent's hard constraints (non-negotiable)
- Agent's soft constraints (negotiable with cost)
- Partner's inferred hard constraints (from background or statements)
- Partner's inferred soft constraints
- Feasible zone: what range of outcomes both parties could accept
- Current gap: how far the agent's ideal outcome is from the partner's inferred acceptable range

## Methodology

- Identify agent's constraints directly from the background profile.
- Infer partner's constraints from their statements, hesitations, or refusals so far.
- Classify each constraint: hard (walk-away condition), soft (preference), or unknown.
- Estimate the feasible zone where both parties' hard constraints are satisfied.
- If no feasible zone exists, flag that the goal may require either concession or creative reframing.

## Pitfalls

- Do not treat soft constraints as hard limits — many can be adjusted with the right framing.
- Do not ignore constraints revealed implicitly through partner hesitation or changed topic.
- Do not confuse the agent's goal with a constraint — goals are desired outcomes, constraints are boundaries.
- Do not fabricate constraints not supported by background or partner statements.

## Switch Rules

- If a constraint is driven by the partner's emotional state, add `emotion`.
- If the constraint analysis reveals a belief gap, add `belief-state`.
- If the analysis directly informs the next tactic, add `intent-strategy`.
