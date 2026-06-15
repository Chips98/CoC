---
name: emotion
description: Use when the task asks about felt emotion, hidden emotion, regulated emotion, mixed emotion, or an unexpected/atypical emotional reaction that contradicts the surface event.
---

# emotion

## Skill Kind

- cognition-node

## Node Role

- Infer felt emotion from how an event bears on the character's desires, goals, and concerns.
- Distinguish visible expression from underlying state when needed.

## When To Use

- Use for emotion, hidden emotion, mixed emotion, regulated emotion, and atypical-reaction items.
- Use when a person's reaction depends on whether an event helps or harms their goals, values, or social standing.

## Required Inputs

- Triggering event summary
- Question
- Relevant beliefs if the emotion depends on mistaken understanding
- The character's desire or goal when the emotion is an appraisal of it

## Output Contract

- Trigger event
- Goal or desire affected
- Most likely emotion state
- Any display-vs-inner-state distinction if needed

## Methodology

- Identify what changed for the character.
- Judge whether that change helps, blocks, threatens, or complicates their goals or desires.
- Infer the likely emotion from that appraisal.
- Keep the answer tied to the exact wording of the question.
- ALWAYS check for contrast signals: 'but', 'however', 'yet', 'although', 'worries', 'concerned about', 'changes life'. These indicate the ACTUAL emotion contradicts the surface event.

## Pitfalls

- Do not confuse personality trait with momentary feeling.
- Do not force extra belief analysis if the event-goal link is already enough.
- Do not ignore masking or regulation cues.
- Do NOT default to joy/happiness just because the surface event is positive. Always check if the character expresses concern or worry that overrides the positive outcome.

## ToMBench UOT (Unexpected Outcome Test) Patterns

### Two-Pass Emotion Analysis
UOT tasks require comparing EXPECTED emotion vs ACTUAL emotion:
1. First pass: What emotion SHOULD the character feel given the surface event?
2. Second pass: What emotion does the character ACTUALLY show/feel?
3. The answer explains WHY the actual emotion differs from the expected one.
- CRITICAL: Always compute BOTH passes. Do not stop at just the actual reaction.

### Common UOT Traps
- "Objectively good event + character worry" → answer is the NEGATIVE emotion (fear, anxiety, embarrassment), not the positive one.
- "Anonymous gift / unknown sender" → curiosity or surprise, NOT embarrassment (unless there's public exposure).
- "First time experience / never imagined" → surprise is usually correct over excitement or curiosity.
- "Unfairness / selfishness discovered" → anger or disappointment, not surprise.
- "Own earlier decision caused the problem" → regret (requires self-blame link).
- "Trusted person betrayed" → betrayal requires CLEAR evidence of disloyalty; mere disappointment or failed help is NOT betrayal.
- "Panic vs embarrassment": panic = invisible pressure, escalating expectations, fear of not coping; embarrassment = social exposure, loss of face.

### Emotion Target Direction
- Always check WHO the emotion is directed at.
- When story contrasts a sacrificing character with selfish others, the parent/elder's emotion is usually directed AT the selfish ones (anger, disappointment), not toward the sacrificing one (touched, grateful).

## Emotion Reversal Pattern (Unexpected Outcome Tasks)

When a positive event is described but the character shows concern:
- Pattern: "[WIN/SUCCESS/GIFT] but [character worries / thinks about consequences / says it changes life]"
- Result emotion: NEGATIVE (fear, anxiety, embarrassment, guilt) — NOT the positive event's expected emotion.
- Examples: winning lottery but fearing life disruption → FEAR; succeeding but not wanting attention → EMBARRASSMENT.
- Rule: when in doubt between a positive and negative emotion, check whether the story mentions any concern, worry, or complication — if yes, choose the negative emotion.

## Discrepant-Emotion Explanation Rule

When the question is 'X should feel A but actually shows B, why?':
- The answer is the option that REFRAMES the situation so that B becomes appropriate.
- ALWAYS reject options that just restate the expected feeling A or its synonyms.
- Common reframings: the other party is more skilled/expert than expected (so curiosity replaces anger); the negative event is actually an opportunity (so calm replaces fear); the apparent loss is small compared to a hidden gain.

## Atypical-Reaction Direction Rule

When a story contrasts a SACRIFICING character with SELFISH others, and asks for the parent/elder's emotion:
- The emotion is usually directed AT the selfish characters (anger, disappointment), not toward the sacrificing one (touched, grateful).
- ALWAYS check WHO the emotion targets before picking a positive feeling.
- NEVER default to "touched" just because someone made a sacrifice — the question may be about anger toward the others.

## Switch Rules

- If the emotion depends on a false belief, add `belief-state` first.
- If the emotion is an appraisal of what the character wants, add `desire` first.
- If the question asks what the emotion leads the person to do, add `action-forecast`.
