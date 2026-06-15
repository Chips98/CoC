---
name: observation-track
description: Use when the answer depends on who observed an event, who missed it, or how access to perceptual evidence differs across characters.
---

# observation-track

## Skill Kind

- cognition-node

## Node Role

- Track perceptual access.
- Build a clean record of who saw, heard, or failed to notice each critical event.

## When To Use

- Use for false-belief, attention, percepts-knowledge, and hidden-information tasks.
- Use when location changes, object swaps, or side conversations happen while one character is absent or distracted.

## Required Inputs

- Event timeline from `fact-extract`
- Question

## Output Contract

- Critical events
- For each event: who observed it, who did not, and any ambiguity
- Visibility or attention gaps that matter for the question

## Methodology

- List the events that change relevant world state.
- For each event, mark observer access explicitly.
- Distinguish being physically present from actually noticing.
- Carry forward only observation gaps that matter for the asked target.
- For hazard/contamination scenarios: explicitly check if the hazard was EXTERNALLY PERCEIVABLE (visible, smellable, audible, tactile) to the character.

## Pitfalls

- Do not jump from seeing to knowing if the event was unclear or ambiguous.
- Do not assume all present characters observed everything.
- Do not answer the question yet unless it is purely about observation itself.
- CRITICAL: Never assume a character could observe something just because it exists in the story. Only treat something as observable if the story describes it as externally detectable.

## ToMBench Observation Patterns

### FBT Observer Isolation
In False Belief Task scenarios with hide-and-move patterns:
- Build a timeline: WHO was present at EACH event.
- Mark the exact moment a character leaves/returns.
- The character who was absent during the move has an OBSERVATION GAP — their belief stays at the pre-move state.
- CRITICAL: "Returning to the room" does NOT mean they saw what happened while away. Only new direct observation updates their knowledge.

### Knowledge-Attention Links
- "Still watching" / "continued to look" = character observed ALL events in that interval.
- Brief side activity (looking at phone, talking to someone) while still in the room ≠ full absence.
- If the character watched all toys being played with, there is NO novelty advantage for any specific toy → gift-giver picks RANDOMLY.

### SIT Observation of Counts
When the story reveals exact counts after checking/counting:
- The revealed count is a NEW observation that updates the character's knowledge.
- Use this exact count for arithmetic, don't rely on the earlier vague quantifier alone.
- Pattern: "most are X" + "after counting, only 5 are Y" → X ≈ total - 5.

## Hazard Observability (for SimpleToM judgment tasks)

When analyzing whether a character could observe a hazard:
- Observable: visibly discolored, obviously moldy, strong smell, broken/damaged packaging, explicitly described as apparent.
- NOT Observable: hidden inside packaging, microscopic organisms, tasteless/odorless poisons, counterfeit items appearing normal, internal contamination not visible from outside.
- If the hazard is NOT described as externally observable → the character COULD NOT have detected it → their actions are based on normal assumptions.

## Switch Rules

- If the question is about what someone knows, add `knowledge-state`.
- If the question is about what someone thinks given missed evidence, add `belief-state`.
