# 0007. Ship a container image; publish it on the server's localhost only

- Status: Accepted
- Date: 2026-10-21
- Decided by: the operator, for issue #27

## Context

Issue #27 packages the app as a container image for the harness's deploy
workflow. Inside a container the app has to listen on `0.0.0.0` so its port can
be published. ADR 0004 kept the API on `127.0.0.1` with no sign-in, and the
README listed "no deployment" as a non-goal. Without sign-in, anyone who can
reach the published port can read and change every task.

## Decision

- The app is built into a container image (`Containerfile`, from the harness
  template) and deployed to the operator's servers through the harness deploy
  path.
- Inside the container, uvicorn listens on `0.0.0.0:$PORT`. On the server the
  port is published on `127.0.0.1` only, with no reverse proxy, so only the
  server itself can reach the app.
- The database lives in the writable `/data` volume (`TODO_DB_PATH=/data/todo.db`).
- The non-goal "no deployment" becomes "no public exposure": the API must not be
  reachable from outside the server until sign-in exists (a new ADR).
- This replaces ADR 0004 only for the container; `make run` still binds
  `127.0.0.1` on the operator's machine.

## Consequences

The app can run on a server with the same image every time, as an unprivileged
user on a read-only filesystem. Keeping it private now depends on how the
server publishes the port, which lives in the deploy setup, not in this
repository; a mistake there exposes an API with no sign-in. Anything running on
the server itself can use the API.

## Alternatives considered

- Local use only, with deployment still a non-goal: safest, but leaves the
  deploy path untried.
- Deploy publicly as it is: anyone on the network could read and change tasks.
- Add sign-in before packaging: right before any public exposure, but more than
  a server-local deployment needs.
