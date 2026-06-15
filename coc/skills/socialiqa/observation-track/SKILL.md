---
name: observation-track
description: Use when a SocialIQA question depends on tracking what was directly witnessed or experienced by a character in the story.
---

# observation-track

## Skill Kind

- cognition-node

## Node Role

- Record what each character directly perceived during the story event.
- Use direct perception to constrain the character's subsequent reaction.

## When To Use

- Use when the story describes what someone saw, heard, received, or experienced directly.
- Use for emotion or next-step questions where the character's perception drives the reaction.

## Required Inputs

- Story context
- Target character (from question)

## Output Contract

- Perceived events: what the target character directly saw, heard, or experienced
- Time of perception: when in the story this happened
- Reaction cue: what aspect of the perception is most likely to drive the answer

## Methodology

- Scan the story for direct perception verbs: saw, heard, felt, received, found, noticed, realized.
- For SocialIQA, the perception is usually the main story event itself.
- Focus on the perception relevant to the named question target.

## Pitfalls

- Do not infer perception from what another character told them; that is indirect.
- Do not extend perception to events that happen after the question's time anchor.

## Switch Rules

- Hand off to `emotion` for feel-questions, `action_forecast` for next-step questions.
