---
name: emotion
description: Use when a Sotopia turn depends on reading the partner's likely feeling, face concern, or hidden pressure so the next move can stay believable and socially effective.
---

# emotion

## Skill Kind

- cognition-node

## Node Role

- Infer the emotional pressure shaping this Sotopia turn.
- Use that reading to choose a response that is believable and socially aware.

## When To Use

- Use when the partner is resisting, hurt, defensive, embarrassed, desperate, or face-sensitive.
- Use when the current turn depends on how hard to push, how much to validate, or whether to de-escalate.

## Required Inputs

- Current observation
- Recent dialogue history
- Goal
- Known relationship pressure

## Output Contract

- Most relevant current feeling or pressure
- How that pressure should change the next move
- Emotional mistake to avoid

## Methodology

- Read the latest turn for signs of fear, anger, shame, urgency, or face protection.
- Decide whether the agent should validate, soften, stay firm, redirect, or close.
- Keep the reading local to the current turn instead of inventing a deep hidden backstory.

## Pitfalls

- Do not psychoanalyze far beyond the visible turn evidence.
- Do not confuse agreement with comfort or resistance with hostility.
- Do not ignore the agent's own goal after acknowledging the partner's feeling.

## Switch Rules

- If the next step depends on negotiation structure, add `intent-strategy`.
- If the turn hinges on what the agent itself wants, add `desire`.
- If the emotional reading needs a final realism check, add `verify`.
