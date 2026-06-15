---
name: emotion
description: Use when a SocialIQA item asks how someone feels, how a person would be described, or which internal reaction best matches the local social event.
---

# emotion

## Skill Kind

- cognition-node

## Node Role

- Infer the most natural SocialIQA feeling or characterization from the current event.
- Distinguish direct inner reaction from traits, evaluations, and consequences.

## When To Use

- Use for `feel`, `feel as a result`, `how would you describe`, and similar SocialIQA items.
- Use when options mix emotions, stable traits, outside judgments, or downstream consequences.

## Required Inputs

- Question
- Options
- Short event summary

## Output Contract

- Target person
- Triggering event
- Best fitting feeling or characterization
- Closest wrong alternative to reject

## Methodology

- Ask what changed for the target person in this local situation.
- Infer the simplest supported reaction from that change.
- For description questions, prefer stable characterization over a fleeting feeling when the wording asks for a trait.
- For feeling questions, prefer the person's subjective reaction rather than another person's opinion of them.

## Pitfalls

- Do not default to pride or happiness after every positive-looking event.
- Do not answer a feeling question with an outside social result.
- Do not turn a brief characterization question into a deep personality diagnosis.

## Switch Rules

- If the reaction depends on false belief or missing information, add `belief-state`.
- If the reaction is mainly an appraisal of what the person wants, add `desire`.
- If the feeling mainly matters because it drives the next action, add `action-forecast`.
- If options stay close after emotion reading, add `verify`.
