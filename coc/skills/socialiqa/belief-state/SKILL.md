---
name: belief-state
description: Use when a SocialIQA question depends on what a character expects or assumes will happen, especially for prerequisite or motive questions.
---

# belief-state

## Skill Kind

- cognition-node

## Node Role

- Identify what the character expects, assumes, or believes at the key moment.
- Use that expectation to explain their motive or predict their next move.

## When To Use

- Use for motive (why-did) questions where the best explanation is based on an expectation or goal.
- Use for prerequisite (before-this) questions where the character had to believe something was necessary.
- Use when a character acts in a way that only makes sense given a specific prior belief.

## Required Inputs

- Story context
- Question

## Output Contract

- Character's belief: what they expected, assumed, or wanted at the relevant moment
- Belief source: what in the story supports this belief (explicit or strongly implied)
- How the belief connects to the answer: how it explains their action or prerequisite

## Methodology

- For SocialIQA, beliefs are usually simple goal-states: the character wanted X, so they did Y.
- Do NOT invoke complex false-belief reasoning unless the story explicitly shows one character lacking knowledge another has.
- Prefer the belief that makes the character's action the most ordinary and obvious continuation.

## Pitfalls

- Do not upgrade a simple desire into a complex strategic belief without story evidence.
- Do not assume the character has a hidden plan unless the story gives a clear signal.

## Switch Rules

- Hand off to `intent_strategy` once the belief is established to derive the motive.
- If the question is purely about emotion, skip to `emotion` directly.
