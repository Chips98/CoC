---
name: verify
description: Use when a Sotopia reply needs one final check for safety, realism, action compatibility, and fit with the current turn objective.
---

# verify

## Skill Kind

- cognition-node

## Node Role

- Run a short final screen on the chosen Sotopia move.
- Catch replies that are unsafe, repetitive, off-goal, or not shaped like a real next turn.

## When To Use

- Use for hard Sotopia turns with relationship risk, negotiation pressure, or repeated conflict.
- Use when the chain already has a candidate move and only needs a final fit check.

## Required Inputs

- Candidate next move
- Current turn objective
- Available actions
- Main safety or relationship constraint

## Output Contract

- Keep or revise
- Concrete reason if revised
- Final approved move

## Methodology

- Check whether the move fits the current turn objective.
- Check whether it is allowed by the available actions.
- Check whether it repeats a failed move without any change.
- Check whether it violates non-violence, realism, or relationship constraints.

## Pitfalls

- Do not rewrite the whole strategy.
- Do not remove needed firmness just to sound nicer.
- Do not approve a move that sounds like a summary instead of a next turn.

## Switch Rules

- If no concrete problem appears, keep the current move.
- If the problem is mainly missing specificity, hand back to `action-forecast`.
