---
name: fact-extract
description: Use when a task first needs a clean list of characters, events, timeline, explicit facts, and answer-relevant surface information before any deeper inference.
---

# fact-extract

## Skill Kind

- cognition-node

## Node Role

- Build the factual base for later reasoning.
- Extract only what is explicitly stated or directly observable from the prompt.

## When To Use

- Use as the first node for most tasks.
- Use when later errors are likely to come from missed characters, missed events, or mixed-up order.
- Do not use this node to infer hidden motives, beliefs, or emotions.

## Required Inputs

- Story or dialogue context
- Question
- Options if available

## Output Contract

- Characters: named entities and role labels
- Event timeline: short ordered steps
- Explicit facts: only text-supported facts
- Answer-relevant surface cues: words, quantities, locations, quoted speech, object changes

## Methodology

- Identify who appears in the scenario and what each person or object does.
- Rewrite the event sequence in short chronological steps.
- Separate explicit facts from later inference.
- Keep only information that may affect the question or option choice.

## Pitfalls

- Do not add hidden intentions or unstated feelings.
- Do not collapse multiple events into one vague summary.
- Do not mix narrator truth with later character belief.

## Switch Rules

- If the question depends on who saw what, add `observation-track`.
- If the question depends on quantities or vague quantifiers, add `constraint-parse`.
- If the question is already answerable from explicit facts, go directly to `option-filter` or answer.
