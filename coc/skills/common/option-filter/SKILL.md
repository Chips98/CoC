---
name: option-filter
description: Use when the system already has enough state information and now needs to eliminate incompatible answer options with short, explicit comparisons.
---

# option-filter

## Skill Kind

- cognition-node

## Node Role

- Convert intermediate reasoning into a clean option decision.
- Remove wrong options with explicit mismatches.

## When To Use

- Use near the end of most multiple-choice tasks.
- Use when earlier nodes already produced enough facts or mental-state conclusions.
- Especially useful when options are semantically close.

## Required Inputs

- Question focus
- Relevant prior node outputs
- Full option list

## Output Contract

- Kept option candidates
- Eliminated options and why each fails
- Final selected option

## Methodology

- Restate the answer target in one line.
- Check each option against that target and prior evidence.
- Eliminate options for one clear mismatch at a time.
- Keep the final justification short and specific.

## Pitfalls

- CRITICAL: Never pick an option just because it matches the surface sentiment of the story (e.g. 'happy story → Joy'). Always check whether the question target contradicts the surface.
- CRITICAL: Do NOT default to option A. Treat A/B/C/D with equal weight. Evaluate every option on its own merit before comparing. If you find yourself leaning toward A without a concrete reason, re-examine B/C/D more carefully.
- ALWAYS re-read the question target before committing: belief vs truth, felt vs expressed, inner vs outward, intention vs outcome, speaker vs listener.
- NEVER eliminate an option on vibes; each elimination must cite one concrete mismatch with a prior-node fact.
- Do not reopen earlier reasoning unless there is a direct contradiction.
- Do not prefer the most eloquent option over the best-supported one.
- Do not keep multiple finalists if the task requires one answer.
- When uncertain between two options, prefer the one tied to concrete story evidence over the one that requires extra assumptions.

## Final Elimination Protocol

Before emitting the final option, run this short checklist:
1. Restate what variable the question asks for in one short clause.
2. For each option, name the single fact or mental-state conclusion it must match.
3. Eliminate options whose required fact is absent or contradicted.
4. If two options survive, prefer the one tied to the character's own perspective, not the narrator's.
5. If a 'surface positive' option and a 'latent negative' option both survive on an emotion/belief item, prefer the latent-negative one when any concern/worry/mismatch cue is present.

## Switch Rules

- If contradiction remains after elimination, add `verify`.
- Otherwise finish with the chosen answer.
