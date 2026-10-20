# 0004. Listen on localhost only, with no sign-in

- Status: Accepted
- Date: 2026-10-20
- Decided by: the operator, during kickoff

## Context

The only user is the operator, on their own machine, and the data is not
sensitive. Sign-in would add secrets and code that the trial does not need.

## Decision

The server binds to `127.0.0.1` and has no authentication. Anyone who can
reach localhost on this machine is trusted.

## Consequences

No secrets to manage and no sign-in code. The API must never be exposed on
another interface as it stands; doing so needs a new ADR that adds sign-in.
Requests from a malicious web page in the operator's browser are an accepted
risk (see the threat model).

## Alternatives considered

- Local network with an API token: reachable from other devices, but adds a
  secret and token checks nobody needs yet.
