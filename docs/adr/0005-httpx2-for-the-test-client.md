# 0005. httpx2 instead of httpx for the test client

- Status: Accepted
- Date: 2026-10-20
- Decided by: the operator, while building the walking skeleton (#1)

## Context

ADR 0002 chose FastAPI's test client with httpx. With Starlette 1.8, using
httpx with the test client is deprecated in favour of httpx2. httpx also pulls
in certifi, and the locked certifi 2026.7.22 has a known vulnerability
(GHSA-6q48-6c7w-9gw2, compromised emSign root CAs) whose fix was released
too recently to pass the 7-day supply-chain cooldown, so `make scan` failed.

## Decision

Use httpx2 (maintained by the Pydantic team) as the dev-only HTTP client for
tests, in place of httpx. This changes only the test-client part of ADR 0002;
the rest of it stands.

## Consequences

The scan passes without loosening the cooldown, and the deprecation warning is
gone. httpx2 verifies certificates with the operating system's trust store
(truststore) instead of a bundled certifi. Nothing in the running app uses it.

## Alternatives considered

- Exempt certifi from the cooldown: loosens a supply-chain gate.
- Keep httpx and wait for the certifi fix to clear the cooldown: blocks the
  skeleton for a week and keeps a deprecated path.
