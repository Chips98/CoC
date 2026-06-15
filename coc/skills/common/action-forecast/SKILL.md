---
name: action-forecast
description: Use when the task asks what a character will do next, where they will search, how they will react, or which behavior follows from their current belief, desire, or emotion.
---

# action-forecast

## Skill Kind

- cognition-node

## Node Role

- Predict next behavior from the smallest sufficient internal state.
- Convert belief, desire, or emotion into likely action.

## When To Use

- Use for behavior prediction, search-location questions, and likely response questions.
- Use after belief, knowledge, emotion, or intention has already been clarified.

## Required Inputs

- Target character state from prior nodes
- Question
- Options if available

## Output Contract

- Target character
- State driving the action
- Most likely next action
- One short reason connecting state to behavior

## Methodology

- Identify the minimum state needed to predict action.
- Ask what action would make sense from that state.
- Prefer the most direct and ordinary behavior unless the prompt says otherwise.

## Pitfalls

- CRITICAL: Do not answer from objective truth if behavior follows false belief.
- ALWAYS pick the action that addresses the immediate failure cause for 'completion of failed actions' items.
- NEVER pick a distracting/relaxing option (going for a walk, reading a book) when the protagonist has just discovered a broken appliance or unfinished task that they care about.
- Do not add extra long explanations.
- Do not substitute your own practical advice for the character's likely action.

## Failure-Recovery Pattern (Completion of Failed Actions)

When the protagonist tries action A and it fails (TV broken, plug fine, but TV still off):
- The next action is the OBVIOUS troubleshooting step that targets the same goal: try a different approach (search online for repair, call repairman, check fuse).
- NEVER pick the option about going outside, reading, talking to a roommate, or any unrelated activity even if the story mentions it as background.
- Background mentions (good weather, roommate hobbies, sunset) are DISTRACTORS, not the answer.

## Multi-Obligation Urgency Rule

When several obligations compete (friend in trouble + tomorrow's competition + helping mom now):
- Pick the action tied to the most TIME-CRITICAL or EXPLICITLY-PROMISED commitment.
- A friend stranded right now who was just promised help outweighs background chores.
- ALWAYS check what the protagonist just said 'I will help' to — they are bound by that promise.

## Switch Rules

- If several options still fit, add `option-filter`.
- If the predicted action contradicts the factual timeline, add `verify`.
