---
name: question-focus
description: Use when the system needs to identify the exact SocialIQA answer target, such as motive, prerequisite, next step, feeling, description, or socially appropriate response.
---

# question-focus

## Skill Kind

- cognition-node

## Node Role

- Restate the exact target of a SocialIQA question in plain terms.
- Prevent the chain from drifting into over-complicated theory-of-mind analysis.

## When To Use

- Use for SocialIQA questions that ask about `why`, `before this`, `what happens next`, `how would you describe`, `how would X feel`, or `what should`.
- Use when all options are plausible commonsense continuations and the main risk is solving the wrong target.

## Required Inputs

- Question
- Options
- Short event summary

## Output Contract

- Question type
- Target person
- Time anchor: before / during / after / next
- What not to answer

## Methodology

- Rewrite the question in one short sentence.
- Identify whether the target is motive, prerequisite, next action, consequence, feeling, trait, or appropriateness.
- Mark the named person whose state or action is being judged.
- State the nearest wrong target to avoid.

## Pitfalls

- Do not convert simple commonsense questions into deep hidden-intent questions without evidence.
- Do not replace the named person with another character.
- Do not answer a result question with a motive, or a motive question with a result.

## Switch Rules

- If the question asks about feelings, hand off to `emotion`.
- If the question asks why someone acts, hand off to `intent-strategy`.
- If the question asks what happens next or what must happen before, hand off to `action-forecast`.
