---
name: option-filter
description: Use when a SocialIQA item needs a final pass to eliminate distractors and select the option most directly supported by the explicit story text.
---

# option-filter

## Skill Kind

- cognition-node

## Node Role

- Remove distractor options that add unsupported assumptions.
- Select the option whose text is most directly grounded in the story.

## When To Use

- Use when two or more options look plausible at first glance.
- Use when one option restates the action while another names a downstream effect or indirect cause.
- Use when an option introduces a person, motive, or constraint not mentioned in the story.

## Required Inputs

- Story context
- Question + three options
- Reasoning from prior nodes (intent_strategy, action_forecast, emotion)

## Output Contract

- Eliminated option(s) with reason (1 sentence each)
- Preferred option with grounding phrase from the story

## Methodology

- For each option: locate the span in the story that directly supports or contradicts it.
- Reject options that require information beyond the given story.
- Reject options that are merely a restatement of the action rather than its cause or consequence.
- Prefer the option whose key noun, verb, or description is closest to the story wording.
- If all options are odd, pick the one that makes the fewest extra assumptions.

## Pitfalls

- NEVER reject an option solely because it names an emotion instead of an action; SocialIQA allows emotion answers.
- NEVER pick the "most responsible adult" answer if the story supports a simpler continuation.
- Do not introduce your own interpretation of what the character "should" do beyond the story evidence.

## Switch Rules

- If the options are very similar, hand off to `verify` for a final tiebreak.
