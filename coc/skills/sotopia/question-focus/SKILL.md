---
name: question-focus
description: Use when the system needs to clarify what the current Sotopia turn requires: the next socially appropriate move for this agent under its goal, relationship constraints, and available actions.
---

# question-focus

## Skill Kind

- cognition-node

## Node Role

- Restate the immediate turn objective for the current Sotopia agent.
- Keep the chain focused on the next move instead of drifting into abstract commentary.

## When To Use

- Use for Sotopia turns where the agent must decide what to say or do next.
- Use when the current turn contains multiple pressures: hidden goal, relationship maintenance, face concerns, safety constraints, and action limits.

## Required Inputs

- Current observation
- Goal
- Available actions
- Short dialogue history

## Output Contract

- Immediate turn objective
- Main social constraint
- Required stance toward the partner
- What would count as off-target this turn

## Methodology

- Rewrite the turn as “What should this agent do right now?”
- Separate long-term goal from the immediate conversational step.
- Note whether the turn should push, soften, clarify, refuse, de-escalate, negotiate, or close.
- Keep the answer target tied to a plausible next utterance or action.

## Pitfalls

- Do not summarize the whole relationship instead of deciding the next move.
- Do not produce a generic moral lecture detached from the current turn.
- Do not ignore available actions or hidden-goal constraints.

## Switch Rules

- If the turn is mainly about hidden feelings and face management, add `emotion`.
- If the turn is mainly about negotiation or persuasion tactics, add `intent-strategy`.
- If the turn needs action filtering or safety checks, add `verify`.
