---
name: action-forecast
description: Use when a SocialIQA item asks what happens next, what someone will do next, or what happens to a named person after the current event.
---

# action-forecast

## Skill Kind

- cognition-node

## Node Role

- Predict the most immediate SocialIQA consequence or next step.
- Keep the answer local, ordinary, and tied to the named person in the question.

## When To Use

- Use for `what will happen`, `what happens next`, `want to do next`, `what does X do next`, and similar SocialIQA questions.
- Use when the main risk is choosing a distant outcome, a different person's reaction, or an over-dramatic escalation.

## Required Inputs

- Question
- Options
- Short event summary

## Output Contract

- Named target person
- Time anchor for the next step
- Most direct next action or consequence
- Main distractor pattern to reject

## Methodology

- Identify whose next action or consequence the question asks about.
- Prefer the nearest realistic continuation of the current event.
- After praise, help, gratitude, apology, or conflict, choose the most socially ordinary next move.
- Keep the prediction grounded in the option text rather than free-form storytelling.

## Pitfalls

- Do not answer another character's reaction when the question asks what happens to the named person.
- Do not jump to a long-range plan when the item only asks for the immediate next result.
- Do not replace a concrete action with a trait, emotion label, or vague life outcome.

## Switch Rules

- If the question is really about motive, hand off to `intent-strategy`.
- If the question is about feelings after the event, hand off to `emotion`.
- If two options are both plausible next steps, add `verify`.
