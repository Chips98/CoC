---
name: action-forecast
description: Use when a Sotopia turn must be turned into the next concrete utterance or action, keeping it realistic, local, and compatible with the available actions.
---

# action-forecast

## Skill Kind

- cognition-node

## Node Role

- Translate the chosen Sotopia tactic into the next concrete move.
- Keep the response shaped like something a person would actually say or do right now.

## When To Use

- Use after the main tactic is clear and the remaining question is what to say or do next.
- Use for turns that require a specific ask, concession, refusal, condition, offer, apology, or closing line.

## Required Inputs

- Current turn objective
- Available actions
- Current observation
- Any important relationship or safety constraint

## Output Contract

- Action type
- Concrete next move
- Why this move fits the turn
- What kind of move would be too vague or off-target

## Methodology

- Choose the smallest concrete move that advances the current turn objective.
- Prefer a clear ask, condition, concession, or boundary over a summary of the whole situation.
- Keep the move consistent with available actions and the latest dialogue turn.
- Make the utterance sound like a live conversational reply, not a narrator note.

## Pitfalls

- Do not output a summary when the scene needs a concrete next move.
- Do not produce a speech that ignores available actions.
- Do not jump several turns ahead in one reply.

## Switch Rules

- If the move still seems unsafe, coercive, or unrealistic, add `verify`.
- If the move depends on reading the partner's current feeling, add `emotion`.
