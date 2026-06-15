---
name: intent-strategy
description: Use when a Sotopia turn needs a dialogue tactic that advances the agent's goal while respecting relationship, safety, and realism constraints.
---

# intent-strategy

## Skill Kind

- cognition-node

## Node Role

- Choose the immediate social tactic for this Sotopia turn.
- Convert long-term goal pressure into one realistic conversational move.

## When To Use

- Use for boundary setting, negotiation, persuasion, de-escalation, repair, or trust-sensitive turns.
- Use when the agent must decide whether to push, soften, clarify, refuse, bargain, or close.

## Required Inputs

- Goal
- Current observation
- Short dialogue history
- Available actions

## Output Contract

- Immediate turn objective
- Chosen tactic for this turn
- Constraint the tactic must respect
- Bad tactic pattern to avoid

## Methodology

- Separate the long-term goal from the one move that should happen now.
- Prefer tactics that move the conversation forward in a believable way.
- If the same ask has already failed, narrow it, ground it, or shift to logistics instead of repeating it.
- If safety, relationship, or face constraints matter, make them explicit in the tactic.

## Pitfalls

- Do not repeat the same rejected demand without changing the terms.
- Do not produce abstract moral commentary instead of a usable turn tactic.
- Do not escalate to threats, revenge, or physical harm when a non-violent route is available.

## Switch Rules

- If the main issue is emotional temperature or face management, add `emotion`.
- If the tactic implies a specific next utterance shape, add `action-forecast`.
- If the turn needs a final safety or realism screen, add `verify`.
