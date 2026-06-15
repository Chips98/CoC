---
name: intent-strategy
description: Use when a SocialIQA item asks why someone acted, what they wanted, or which socially appropriate response best fits the local situation.
---

# intent-strategy

## Skill Kind

- cognition-node

## Node Role

- Infer the simplest supported motive behind a SocialIQA action.
- Keep explanation questions tied to the local trigger instead of broad personality theories.

## When To Use

- Use for `why did`, `why would`, `what should`, `best way`, and other motive or socially appropriate response items.
- Use when options mix direct motives, downstream effects, and paraphrases of the same action.

## Required Inputs

- Question
- Options
- Short event summary

## Output Contract

- Actor goal
- Immediate trigger
- Best local explanation or social tactic
- Wrong-but-nearby interpretation to avoid

## Methodology

- Identify the concrete action that needs an explanation.
- Choose the motive that directly causes that action in the story.
- Prefer simple social motives over hidden strategic planning unless the story clearly supports strategy.
- For should or best-way questions, prefer the option that is both socially appropriate and practically useful.

## Pitfalls

- Do not answer a why-question with the action's later result.
- Do not pick an option that merely restates the action without explaining it.
- Do not upgrade ordinary everyday motives into deception, manipulation, or multi-step planning without evidence.

## Switch Rules

- If the action is indirect or hint-based, add `pragmatics`.
- If the motive mainly depends on the person's feeling, add `emotion`.
- If the motive predicts a concrete next step, add `action-forecast`.
