---
name: pragmatics
description: Use when a SocialIQA question involves social norms, politeness, social evaluation, or implied meaning beyond the literal action.
---

# pragmatics

## Skill Kind

- cognition-node

## Node Role

- Interpret the social or normative layer of the story event.
- Identify the implied evaluation, obligation, or relational consequence.

## When To Use

- Use for characterization questions (how-would-you-describe).
- Use for social-norm questions (what-should / best-way).
- Use when the options include traits, evaluations, or normative labels rather than pure actions or emotions.

## Required Inputs

- Story context
- Question and options

## Output Contract

- Social norm: what norm or expectation is relevant in this scene
- Implied evaluation: how observers or the social context would judge the action
- Most supported option type: trait / temporary state / role label / evaluation

## Methodology

- SocialIQA characterization answers can be temporary states (embarrassed, proud) OR stable traits (caring, selfish).
- Check which option type best matches the story's evidence level: brief events → temporary state; repeated patterns → stable trait.
- For social-norm answers, prefer the option that is both socially appropriate AND practically helpful in the described situation.

## Pitfalls

- Do not force a stable personality trait when the story only describes one brief incident.
- Do not favor the most morally ideal answer when the question asks what a specific person actually did or would do.

## Switch Rules

- If the question is really about an action rather than a social evaluation, hand off to `action_forecast`.
- If the question is about emotion rather than evaluation, hand off to `emotion`.
