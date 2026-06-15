---
name: knowledge-state
description: Use when a Sotopia turn requires mapping what each party knows, what is private, and what was newly revealed so the agent can reason about information asymmetry before choosing its next move.
---

# knowledge-state

## Skill Kind

- cognition-node

## Node Role

- Map the information landscape for this Sotopia interaction.
- Separate public knowledge, agent-private knowledge, and partner-private knowledge.
- Identify what was just revealed or newly learned this turn.

## When To Use

- Use at the start of an interaction to set up information asymmetry.
- Use after a partner statement that reveals new facts about their constraints, preferences, or limits.
- Use when deciding whether to probe, share, or guard information.
- Use when the partner says something that contradicts what the agent thought they knew.

## Required Inputs

- Background / scenario context
- Agent's private goal and secret constraints
- Partner's most recent statements
- Conversation history summary

## Output Contract

- Public knowledge (both parties know this)
- Agent-private knowledge (only agent knows)
- Partner-private knowledge (inferred from their behavior, may be incomplete)
- New information revealed this turn
- Information leverage: what the agent can use or protect

## Methodology

- Read the background context to establish the initial public/private split.
- Scan the latest turn for any new fact disclosures from the partner.
- Update the knowledge map: what is now shared that was not before?
- Identify whether the newly revealed information helps or hurts the agent's goal.
- Decide if this turn should include a strategic probe to uncover more partner-private knowledge.

## Pitfalls

- Do not treat inferred partner knowledge as confirmed fact.
- Do not share agent-private information unless it tactically advances the goal.
- Do not ignore information revealed in earlier turns — maintain continuity.
- Do not conflate "partner didn't mention X" with "partner doesn't know X."

## Switch Rules

- If knowledge gap maps onto a belief the partner is acting on, add `belief-state`.
- If the newly learned information changes the turn tactic, add `intent-strategy`.
- If a specific piece of information should be concealed, add `verify`.
