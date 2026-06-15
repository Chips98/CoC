---
name: verify
description: Use when a SocialIQA item has two close commonsense options and the chain needs one last check on target person, time anchor, and option fit.
---

# verify

## Skill Kind

- cognition-node

## Node Role

- Run a short final check for the exact SocialIQA target.
- Catch mistakes where the answer drifts to the wrong person, wrong time, or wrong question type.

## When To Use

- Use when two SocialIQA options both sound reasonable.
- Use after motive, feeling, or next-step analysis when the remaining risk is target mismatch rather than missing facts.

## Required Inputs

- Current best answer
- Question focus summary
- One-line state summary from earlier nodes

## Output Contract

- Keep or revise
- Exact mismatch if revised
- Final answer after the check

## Methodology

- Re-check who the question is about.
- Re-check whether the question asks about motive, prerequisite, feeling, trait, or next step.
- Re-check whether the option stays close to the local story event.

## Pitfalls

- Do not reopen the whole story.
- Do not invent new hidden assumptions.
- Do not switch answers unless a clear target mismatch is found.

## Switch Rules

- If no concrete mismatch appears, keep the current answer.
- If the mismatch is actually about question type, hand back to `question-focus`.
