---
name: observation-track
description: Use when a Sotopia turn requires understanding the trajectory of the conversation so far — what has been agreed, refused, avoided, or left open — before deciding the next move.
---

# observation-track

## Skill Kind

- cognition-node

## Node Role

- Track the meaningful state of the conversation across recent turns.
- Identify what has shifted, what has stalled, and what opportunity has opened.
- Provide a compact progress map for downstream strategy selection.

## When To Use

- Use when the conversation has 3+ turns and history needs to be synthesized.
- Use when the agent has made a request that was refused and needs to reframe.
- Use when the partner has changed their position and the agent should notice.
- Use before any strategy pivot or closing move.

## Required Inputs

- Full dialogue history (or last 4–6 turns minimum)
- Agent's goal
- Agent's previous asks and the partner's responses to them

## Output Contract

- Conversation phase: opening / probing / negotiating / closing / stuck
- What the agent has already tried and the partner's response
- What the partner has revealed about their position or limits
- Current opening: the best available angle for this turn
- Dead ends: approaches the partner has already rejected

## Methodology

- Scan history for explicit agreements, explicit refusals, and implicit signals.
- Classify the current phase based on how many substantive exchanges have occurred.
- Note any softening or hardening in the partner's position over recent turns.
- Flag repeated failed attempts — the agent must not repeat them unchanged.
- If the partner has just shifted their position positively, flag this as an opening to close.

## Pitfalls

- Do not conflate "partner hasn't refused yet" with "partner agrees."
- Do not ignore a pattern of soft rejections across multiple turns.
- Do not restart the analysis from scratch each turn — build on the previous understanding.
- Do not assume the opening turn strategy is still optimal in later turns.

## Switch Rules

- If tracking reveals emotional escalation, add `emotion`.
- If the phase calls for a major strategy shift, add `intent-strategy`.
- If a previous attempt was close to succeeding, add `action-forecast` to refine the next move.
