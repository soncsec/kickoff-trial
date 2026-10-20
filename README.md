# kickoff-trial

A small to-do list HTTP API for one local user. It exists to try out the
claude-harness workflow end to end, from kickoff to a finished milestone.

## Why

The harness promises that an agent can take a project from an idea to merged,
tested features through issues, pull requests and CI, without breaking its
guardrails. A to-do API is small enough to finish quickly but still needs
storage, input validation and tests, so it exercises the whole path.

"Working" means the first milestone's features are merged through
issue → pull request → green CI, with no guardrail violations.

## Non-goals

- No accounts or sign-in: one local user.
- No deployment: it runs on the operator's machine only.
- No web pages or frontend: HTTP API only.
- No external services or secrets.

## Status

Early development. [ROADMAP.md](ROADMAP.md) has what comes next.

## Getting started

<!-- The walking skeleton fills in how to run the server. -->

```sh
make setup   # install dependencies exactly as locked
make check   # lint, tests and scans: what CI runs
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Decisions](docs/adr/)
- [Threat model](docs/threat-model.md)
- [Security policy](SECURITY.md)
