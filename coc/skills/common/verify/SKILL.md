---
name: verify
description: Use when the chain needs a final lightweight consistency check for perspective, timeline, option fit, or contradiction, especially on harder or easily confused tasks.
---

# verify

## Skill Kind

- cognition-node

## Node Role

- Run a small final check without reopening the whole chain.
- Catch perspective drift, timeline errors, and answer-target mismatch.

## When To Use

- Use only when there is real uncertainty, close options, or known failure patterns.
- Prefer on complex social reasoning, mixed benchmark items, or after long chains.
- Do not use by default on easy questions.

## Required Inputs

- Proposed answer
- Question focus
- Minimal prior state summary

## Output Contract

- Pass or revise
- If revise: exact contradiction or mismatch
- Final answer after check

## Methodology

- Re-check the target perspective.
- Re-check time markers and observation access.
- Re-check that the chosen option matches the asked variable, not a nearby one.
- Revise only if a concrete contradiction is found.

## Pitfalls

- Do not regenerate the entire reasoning chain.
- Do not introduce new speculative analysis.
- Do not change the answer without a specific conflict.

## Switch Rules

- If no contradiction is found, keep the current answer.
- If a contradiction is found, revise once and stop.
