---
name: belief-state
description: Use when a Sotopia turn requires tracking what the partner believes, what they don't yet know, or where their mental model diverges from reality so the agent can exploit or respect that gap strategically.
---

# belief-state

## Skill Kind

- cognition-node

## Node Role

- Track the partner's current belief state across the dialogue history.
- Identify gaps between what the partner believes and what the agent knows.
- Use belief gaps strategically: decide when to correct, when to exploit, or when to reveal.

## When To Use

- Use when the partner is acting on an assumption the agent knows to be wrong.
- Use when the agent holds private information that affects the partner's likely choices.
- Use when the partner's past statement implies a belief the agent needs to acknowledge or challenge.
- Use when deciding how much to disclose about the agent's own goals or constraints.

## Required Inputs

- Agent's private goal and hidden information
- Partner's recent statements and observable actions
- Known gaps between agent's information and what was shared

## Output Contract

- Partner's current operating belief (what they think is true)
- Key belief gap (what they don't know that matters to this turn)
- Agent's decision: reveal / conceal / correct / exploit this gap
- Risk of current belief gap being discovered

## Methodology

- Reconstruct the partner's model of the situation from their statements alone.
- Identify one specific belief gap that is most relevant to the current turn goal.
- Choose a stance: if revealing closes the deal, disclose; if concealing preserves leverage, stay quiet.
- Do not volunteer private information when the partner hasn't asked and disclosure hurts the agent's goal.
- If the partner is about to make a decision based on a false belief, consider whether correction serves long-term relationship and goal.

## Pitfalls

- Do not assume the partner knows everything the agent knows.
- Do not assume the partner is lying when they could just be uninformed.
- Do not reveal all private information just to "be honest" if it undermines the agent's hidden goal.
- Do not confuse the partner's stated preference with their underlying belief.

## Switch Rules

- If the belief gap is about emotional state or face, add `emotion`.
- If the gap affects the agent's tactic this turn, pass finding to `intent-strategy`.
- If verification that the reply respects the belief boundary is needed, add `verify`.
