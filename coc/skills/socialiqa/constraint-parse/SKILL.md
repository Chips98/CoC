---
name: constraint-parse
description: Use to identify the query type of a SocialIQA question (next-step, emotion, motive, prerequisite, description, consequence) so the rest of the chain stays on track.
---

# constraint-parse

## Skill Kind

- cognition-node

## Node Role

- Classify the question into one of the core SocialIQA query types.
- Extract the answer scope: who, what kind of thing, at what point in time.

## When To Use

- Use when the question wording is ambiguous about whether it asks for an action, emotion, motive, or description.
- Use before `action_forecast` or `emotion` to prevent them from answering the wrong query type.

## Required Inputs

- Question text
- Options (to detect the expected answer type from option phrasing)

## Output Contract

- query_type: one of [next_step | emotion_after | motive | prerequisite | characterization | consequence | social_norm]
- answer_target: the named person or group the question asks about
- time_anchor: before / during / after the main event

## Methodology

- Parse the first 4 words of the question to identify the query type:
  - "what will / does / did X do next" → next_step
  - "how does/will X feel" or "how would X feel" → emotion_after
  - "why did / would X" → motive
  - "what did X need to do before" → prerequisite
  - "how would you describe X" → characterization
  - "what will happen to X" → consequence
  - "what should X do" or "best way for X" → social_norm
- Cross-check with the option phrasing: if options are all verbs, it is likely next_step; if all emotions/adjectives, likely emotion_after.

## Pitfalls

- NEVER label a prerequisite question as a next_step question.
- NEVER confuse "what happened to X" (consequence about X) with "what did X do" (next_step of X).

## Switch Rules

- Hand off directly to the node matching the identified query_type.
