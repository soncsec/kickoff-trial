# 0001. Record architecture decisions

- Status: Accepted
- Date: 2026-10-20
- Decided by: the operator, during kickoff

## Context

Agents and people working on this project later need to know why things are the
way they are, not only what they are.

## Decision

We keep Architecture Decision Records in `docs/adr/`, one per significant
decision, numbered in order. An accepted ADR is never edited: a new ADR
replaces it and says so, and the old one's status becomes "Replaced by NNNN".

## Consequences

Decisions and their reasons stay findable next to the code. Each significant
change costs one short extra file.

## Alternatives considered

- Decisions in pull request descriptions only: hard to find later.
- A single decisions log file: grows unwieldy and invites edits to old entries.
