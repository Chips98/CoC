---
name: intent-strategy
description: Use when the task asks why a character said or did something, how they try to influence others, or which persuasion or interaction strategy best explains an action.
---

# intent-strategy

## Skill Kind

- cognition-node

## Node Role

- Infer the purpose behind an action or utterance.
- Identify the strategy used to move another person's belief, choice, or response.

## When To Use

- Use for intention, persuasion, explanation-of-action, and discrepant-intention tasks.
- Use when the answer depends on the practical goal behind an utterance rather than its literal content alone.

## Required Inputs

- Event or dialogue summary
- Question
- Relevant beliefs, desires, or social context if available

## Output Contract

- Actor goal
- Immediate tactic or strategy
- Target of the strategy
- Why this strategy fits better than nearby alternatives

## Methodology

- Identify what the actor appears to want to achieve.
- Connect the utterance or action to a concrete influence tactic.
- Compare literal wording with likely practical aim.
- Keep the inferred strategy as simple as the data allows.
- For persuasion tasks: identify the MECHANISM type, not just the content.

## Persuasion Strategy Taxonomy (for ToMBench PST)

Match the strategy to these canonical types:
1. PROMISE / REWARD — "If you do X, I will give you Y" or "You will benefit from X."
2. EMOTIONAL APPEAL — "Think of the feelings/suffering/love involved." Exploits sympathy, fear, or affection.
3. LOGICAL ARGUMENT — "Because X is true, therefore Y." Uses evidence, facts, or reasoning chains.
4. DIRECT REQUEST — Simply asks or commands without elaborate justification.
5. SOCIAL PROOF — "Everyone else does X" or "People like us choose Y."
6. PRESSURE / THREAT — "If you don't do X, something bad will happen."
7. AUTHORITY — "As an expert/parent/leader, I say X."

When identifying a strategy: ignore the specific content; focus on the persuasion MECHANISM.

## Pitfalls

- CRITICAL: Never mistake outcome for intention. A failed action still had a specific goal — answer with the goal, not the result.
- ALWAYS answer 'why' questions with the practical GOAL behind the action, not a description of the action itself.
- NEVER pick the literal-content option for PST items — always map to one of the 7 persuasion mechanisms.
- Do not overread sarcasm or hidden hostility when a straightforward tactic fits.
- Do not ignore the exact question target if it asks "how" rather than "why".

## ToMBench PST (Persuasion Story Task) Patterns

### Persuasion Target Matching
The correct persuasion strategy DIRECTLY addresses the listener's stated concern:
- If listener worries about cost → address cost (compromise, reduce scope, show value).
- If listener worries about risk → address risk (reversible trial, safety net, evidence).
- If listener has value/identity conflict → reframe the value, don't attack it.
- CRITICAL: Do NOT pick generic "try it and see" or "bring a famous example" when a direct explanation addressing the specific concern is available.

### Listener Type Adaptation
- Young child / sibling / rebellious teen → low-pressure, interest-linked, small immediate request beats adult-style lecturing.
- Authority figure (parent/teacher/boss) → evidence-based, respectful reframing beats emotional appeal.
- Peer with operational concern → reversible pilot or compromise beats abstract endorsement.

### Common PST Traps
- Picking the most elaborate or "scientific" strategy when a simple direct request fits better.
- Picking "experience it yourself" when the dispute is about values/identity (not about practical uncertainty).
- Attacking the listener's current values as shallow — broadening the definition is safer than insulting it.

## Switch Rules

- If the meaning is indirect or socially coded, add `pragmatics`.
- If the intention predicts later behavior, add `action-forecast`.
