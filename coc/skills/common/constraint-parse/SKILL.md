---
name: constraint-parse
description: Use when a task depends on quantities, temporal order, vague quantifiers, exclusivity, ranges, or other explicit logical constraints that must be normalized before choosing an answer.
---

# constraint-parse

## Skill Kind

- cognition-node

## Node Role

- Translate loose wording into usable constraints.
- Normalize quantities and ordering before any psychological inference is attempted.

## When To Use

- Use for phrases like "most", "some", "almost none", "before", "after", "only", "at least", and "at most".
- Use for counting, elimination, scalar implicature, and sequence questions.
- Prefer this node over belief or intent analysis for arithmetic or quantifier-heavy items.

## Required Inputs

- Factual summary from `fact-extract`
- Question
- Options if available

## Output Contract

- Total known quantities
- Parsed constraints
- Open variables
- Allowed value range or logical relations

## Methodology

- Convert natural-language quantifiers into explicit bounds or relations.
- Track totals, subsets, exclusions, and leftovers.
- Separate what is known before checking from what is known after checking.
- Preserve uncertainty when the text does not fully determine one value.

## Pitfalls

- Do not invent exact numbers when the prompt gives only ranges.
- Do not switch from logical constraints to character psychology unless the question explicitly asks for belief.
- Do not ignore time markers such as "before checking" and "after checking".

## Switch Rules

- If the question asks what a character would guess under incomplete information, add `belief-state` after this node.
- If parsed constraints are enough to remove wrong options, pass to `option-filter`.
