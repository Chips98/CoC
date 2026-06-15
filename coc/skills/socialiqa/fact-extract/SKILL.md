---
name: fact-extract
description: Use at the start of a SocialIQA chain to extract the key social facts from the short context: who did what, to whom, in what setting, and what the outcome was.
---

# fact-extract

## Skill Kind

- cognition-node

## Node Role

- Extract the minimal social facts needed to answer the question.
- Identify the agent (who acted), the target (who is affected), the action, and the immediate outcome.

## When To Use

- Use as the first step when the context contains multiple characters or multiple events that could be confused.
- Use when the question asks about a specific named person so the chain stays focused on that person.

## Required Inputs

- Short social context
- Question (to identify the target character and query type)

## Output Contract

- Agent: who performed the main action
- Target: who the question is asking about
- Action: what was done
- Outcome: immediate result visible in the story

## Methodology

- Read the context sentence by sentence; extract entities and their roles.
- Do NOT add information beyond the story text.
- Note the time order: before / during / after the main action.
- Identify which character(s) the question directly asks about.

## Pitfalls

- Do not conflate the agent with the target when the question asks about a different person.
- Do not include long-run consequences that are not stated in the context.
- Keep the extraction brief; this is just scaffolding for later nodes.

## Switch Rules

- Hand off to `question_focus` to clarify the query type, or directly to `intent_strategy` / `emotion` / `action_forecast` depending on the question word.
