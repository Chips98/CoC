---
name: pragmatics
description: Use when the task depends on non-literal meaning, hinting, faux pas, politeness, irony, sarcasm, or the gap between literal wording and intended social meaning.
---

# pragmatics

## Skill Kind

- cognition-node

## Node Role

- Interpret socially intended meaning rather than literal wording alone.
- Evaluate whether speech fits or violates conversational and social norms.

## When To Use

- Use for hinting, faux pas, irony, sarcasm, inappropriate speech, and indirect communication tasks.
- Use when literal sentence meaning is not enough to choose the answer.

## Required Inputs

- Dialogue or utterance summary
- Question
- Relevant speaker-hearer knowledge if available

## Output Contract

- Literal content
- Intended social meaning
- Social norm or expectation involved
- Why the utterance is appropriate, inappropriate, indirect, or face-saving

## Methodology

- Start with the literal sentence meaning.
- Compare it with the social context and shared knowledge.
- Infer the intended meaning or norm violation.
- Keep the interpretation anchored to concrete context, not abstract theory.
- For faux pas tasks: explicitly identify (a) who spoke, (b) what sensitive information they lacked, (c) why the statement was hurtful despite innocent intent.

## Pitfalls

- Do not assume all indirect language is sarcasm.
- Do not ignore who knows which background fact.
- Do not over-upgrade to complex multi-agent modeling unless the utterance really requires it.
- For 'Does X know' questions in faux pas tasks: do NOT assume the SPEAKER of the faux pas knows — they almost certainly did NOT know (that's why they committed the faux pas).

## Faux Pas Analysis Framework

When analyzing faux pas scenarios, explicitly answer these 4 questions:
1. WHO spoke the potentially inappropriate utterance? (the SPEAKER)
2. WHO was hurt by it? (the LISTENER/recipient)
3. What sensitive fact did the SPEAKER NOT know? (their ignorance = the faux pas trigger)
4. What sensitive fact DID the LISTENER know? (their awareness = why they were hurt)

Then apply: SPEAKER→did NOT know; LISTENER→DID know.
This directly resolves 'Does X know?' questions by identifying X's role (speaker vs. listener).

## ToMBench Pragmatics Sub-Type Patterns

### Scalar Implicature (SIT)
When the story uses quantifiers like "most", "some", "a few", "almost all":
- "most" → 60%-80% of total (NOT bare majority like 51%)
- "a few" → 2-3 items
- "several" → 3-5 items
- "almost all" → 90%+ of total
- "very few" → 1-3 items
- CRITICAL: When total count and a minority count are both given, compute the majority by arithmetic: majority ≈ total − minorities. Pick the option closest to that estimate.
- Do NOT default to the weakest interpretation when stronger numeric evidence is available.

### Hinting Task
When a speaker makes an indirect statement:
- The intended meaning is usually a REQUEST or REFUSAL, not a literal observation.
- Pattern: "I have [obligation/constraint] tomorrow" → polite refusal or request to stop current activity.
- Pattern: "It's getting [late/cold/expensive]" → indirect request to leave/stop/change.
- NEVER interpret hints as literal information sharing unless the context clearly supports it.

### Faux Pas Recognition
- A faux pas requires: (1) speaker says something, (2) speaker did NOT know a sensitive fact, (3) the statement touches that sensitive fact and hurts the listener.
- If no sensitive hidden fact exists AND the statement is not directly insulting → NO faux pas.
- Direct insults, put-downs, or humiliating judgments count as inappropriate even without hidden facts.
- Judge the SPOKEN WORDS only, not the situation (a dangerous gift is not a faux pas if nothing inappropriate was said).

### Sarcasm / Irony
- Look for mismatch between literal meaning and context.
- The intended meaning is usually the OPPOSITE of the literal statement.
- Check tone markers: "Oh, great", "How wonderful", "Thanks a lot" in negative contexts.

## Switch Rules

- If the utterance reveals a speaker goal, add `intent-strategy`.
- If the answer options can now be pruned, pass to `option-filter`.
