---
name: question-focus
description: Use when the system needs to restate what the question is really asking, prevent answer drift, or distinguish between similar targets such as truth, belief, intention, action, or source.
---

# question-focus

## Skill Kind

- cognition-node

## Node Role

- Pin down the exact answer target before deeper reasoning starts.
- Prevent the chain from solving a neighboring but wrong problem.

## When To Use

- Use when options look similar or the question wording is easy to misread.
- Use when the task may confuse objective truth, character belief, emotional display, future action, or speech function.
- Especially useful for ToMBench mixed subtasks and multi-sentence prompts.

## Required Inputs

- Question
- Options if available
- Minimal factual summary from `fact-extract`

## Output Contract

- Target variable: what must be predicted or judged
- Target holder: which character, object, or utterance the question refers to
- Required perspective: narrator, actor, observer, or listener
- Disallowed shortcuts: nearby but wrong interpretations to avoid

## Methodology

- Rewrite the question in one short sentence.
- Identify the entity whose state or action must be judged.
- Mark the needed viewpoint.
- List the most likely ways to answer the wrong thing.

## Pitfalls

- Do not start re-solving the whole task here.
- Do not repeat all story facts.
- Do not ignore option wording if options impose a narrower target.

## Switch Rules

- If the target depends on a person's visible or hidden mental state, add the matching mental-state node.
- If the target is direct factual recovery, hand off to `option-filter`.
