---
name: knowledge-state
description: Use when a SocialIQA question depends on what a character knows or does not know at the time of their action.
---

# knowledge-state

## Skill Kind

- cognition-node

## Node Role

- Track what each character actually knows from the story context.
- Use that knowledge boundary to constrain action and emotion predictions.

## When To Use

- Use when a character's action can only be explained by what they knew at that moment.
- Use for prerequisite questions where the character had to acquire knowledge before acting.
- Use when the story specifies that one character is unaware of a fact another character knows.

## Required Inputs

- Story context
- Question

## Output Contract

- Character: who the knowledge question concerns
- Known facts: list of facts the character knows at the relevant time point
- Unknown facts: list of facts the character does not know

## Methodology

- For SocialIQA, knowledge states are usually simple: characters know what happened directly to them or around them.
- Do not attribute hidden knowledge unless the story says "X found out" / "X was told" / "X saw."
- Keep the knowledge list short (2-4 items); SocialIQA contexts are brief.

## Pitfalls

- Do not over-complicate knowledge tracking; SocialIQA does not usually test explicit false-belief reasoning.
- Do not assume a character knows something just because the reader knows it.

## Switch Rules

- Hand off to `belief_state` only if the question explicitly asks about a character's expectation or assumption.
- Otherwise hand off directly to `action_forecast` or `emotion`.
