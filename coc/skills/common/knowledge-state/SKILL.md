---
name: knowledge-state
description: Use when the task depends on what a character knows, does not know, or can infer from direct access to information, without requiring richer motive analysis.
---

# knowledge-state

## Skill Kind

- cognition-node

## Node Role

- Model explicit knowledge and ignorance.
- Keep knowledge grounded in direct evidence or clear communication.

## When To Use

- Use for knowledge-link tasks, source-of-information questions, and simple epistemic reasoning.
- Use when the question asks whether someone knows a fact, object identity, location, or source.

## Required Inputs

- Factual summary from `fact-extract`
- Observation record from `observation-track` if available
- Question

## Output Contract

- Character-by-character knowledge table
- Unknown facts for each relevant character
- Direct evidence or communication path for each known fact

## Methodology

- Mark which facts each character can support from perception or testimony.
- Separate "knows" from "has not been shown".
- Keep the representation simple and local to the question target.
- For each relevant hazard/fact: ask explicitly "Could the character have perceived this through normal senses?"

## Pitfalls

- Do not over-upgrade to full belief recursion if the task only asks knowledge.
- Do not treat reasonable guesses as confirmed knowledge.
- Do not import facts only the narrator knows unless the character has access.
- CRITICAL: Never assume a character knows something just because the narrator/reader knows it. Only attribute knowledge that follows from what the character could directly observe or was explicitly told.

## Epistemic Judgment (SimpleToM Judgment tasks)

When the question asks whether a character's action was "Reasonable" given their knowledge:
- Step 1: List what the character COULD perceive (visible, smellable, audible, tangible).
- Step 2: Determine if the hazard/risk was detectable by those senses.
- Step 3: If the hazard was NOT detectable (hidden, microscopic, tasteless, inside packaging) → the character COULD NOT have known → their action is REASONABLE.
- Step 4: If the hazard WAS physically apparent → the character SHOULD have noticed → action may be NOT REASONABLE.
- Apply the character's epistemic state strictly — never judge from the omniscient narrator perspective.

## Limited-Experience / Pretend-Play Rule

When the story explicitly says a character "knows nothing about X" or "lives somewhere with no X" (no trees, no plants, no animals, no humans, etc.):
- The character CANNOT be imitating X, even if their action visually looks like X.
- ALWAYS pick the option whose subject comes from the character's actual environment.
- NEVER pick any option that names the absent category (trees, plants, etc.).

## Quantitative Scalar Inference Rule

When the story gives a TOTAL count and uses scalar quantifiers ('most', 'a few', 'one or two', 'very few') for the categories, then reveals the actual count of one minority category:
- Compute majority ≈ total − sum(minorities). Use 'one or two' ≈ 1–2, 'a few' ≈ 3–6, 'very few' ≈ 1–5.
- Pick the option closest to that arithmetic estimate.
- NEVER pick the option that simply equals (total − revealed_count) if there are multiple minority categories.

## Attention-Links Rule

When a character is physically present and the story says they 'still watched', 'continued to look', or otherwise maintained attention while others played:
- Treat them as having OBSERVED every event in that interval, even if they were doing something else.
- For 'what does the gift-giver do?' questions, if all candidate items were seen by the recipient, the giver picks RANDOMLY (no novelty advantage).
- NEVER assume an absence-of-attention from a brief side activity if the story explicitly says the character continued watching.

## Switch Rules

- If the task asks what the character would think or do under incomplete knowledge, add `belief-state` or `action-forecast`.
- If knowledge directly decides the answer, pass to `option-filter`.
