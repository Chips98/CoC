---
name: belief-state
description: Use when the answer depends on what a character would believe given incomplete, outdated, or asymmetric information, including first-order false-belief reasoning.
---

# belief-state

## Skill Kind

- cognition-node

## Node Role

- Infer the character's current working belief from their accessible evidence.
- Handle false beliefs and perspective mismatch.

## When To Use

- Use for false-belief tasks and belief-based action prediction.
- Use when the question is about what a character thinks, expects, searches for, or assumes.
- Use after `observation-track` or `knowledge-state` when possible.

## Required Inputs

- Relevant facts
- Observation and knowledge gaps
- Question

## Output Contract

- Target character belief
- Evidence available to that character
- Missing evidence causing belief mismatch
- Optional secondary belief only if strictly needed

## Methodology

- Start from the target character's last available evidence.
- Ignore world-state updates they did not access.
- Build the simplest belief statement that answers the question.
- Only add nested belief if the question explicitly requires it.

## Pitfalls

- Do not default to higher-order recursion.
- CRITICAL: Never answer from narrator ground truth. Always compute from the target character's last observed state — if they missed an event, the world stays as they remember it.
- ALWAYS apply the 'last seen location' rule: for 'where will X look / search / fetch' questions, X will go to where X last saw the object, even if it has since been moved.
- Do not add motive analysis unless the question is really about intention.

## False-Belief Reversal Pattern

When the story contains a hidden move (object displaced while a character is away, absent, or distracted):
- Identify the character who was NOT present for the move (the belief-holder).
- That character's belief = the pre-move state.
- If the question asks where they will act, they act on the pre-move state, not the post-move truth.
- NEVER pick the option that describes the current real location if the character did not witness the move.

## ToMBench FBT Trap Patterns

### Trap 1: Hide-and-Move
Story pattern: "A and B find object in Location1. A leaves. B moves object to Location2."
- If question asks where A will look → answer is Location1 (A's last seen location).
- If question asks where the object actually is → answer is Location2.

### Trap 2: Second-Party Return
Story pattern: "A leaves, B moves object, then A returns."
- A's belief is STILL the pre-move state unless the story explicitly says A saw the new location.
- Do NOT assume returning = re-observing.

### Trap 3: Double-Layer Belief Nesting
Story pattern: "What does A think B thinks about X?"
- Only go to second-order belief if the question explicitly asks about nested beliefs.
- For simple "where will A look" questions, stay at first-order.

### Trap 4: Pretend-vs-Reality Layer
Story pattern: "A pretends X is Y" or "In the game, X is Y."
- Separate pretend-world beliefs from real-world beliefs.
- If the question asks about the pretend scenario, answer within that frame.
- If the question asks about reality, ignore the pretend layer.

### Trap 5: Content False Belief (Container Label)
Story pattern: "A finds a box labeled 'cookies'. A opens it and finds pencils. B enters later."
- B (who never opened the box) expects the label content (cookies).
- A (who opened it) knows the real content (pencils).
- CRITICAL: If the question asks "what should be inside" or "what does B expect" → answer from label.
- If the question asks "what is actually inside" → answer the real content.

## Switch Rules

- If the question asks what the character will do next, add `action-forecast`.
- If the belief alone separates options, send to `option-filter`.
