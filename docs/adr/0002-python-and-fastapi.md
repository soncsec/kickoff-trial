# 0002. Python with FastAPI for the HTTP API

- Status: Accepted
- Date: 2026-10-20
- Decided by: the operator, during kickoff

## Context

The project is a small JSON HTTP API whose main purpose is to exercise the
harness workflow. The harness defaults to Python managed by uv.

## Decision

Python, managed with uv, using FastAPI for routing and Pydantic validation,
uvicorn to serve it, and FastAPI's test client (httpx) for tests.

## Consequences

Request validation and error responses come for free, and tests can call the
app in-process. It adds a few dependencies (FastAPI, uvicorn, httpx) to keep
locked and scanned.

## Alternatives considered

- Standard library `http.server`: no dependencies, but validation, routing and
  error handling would all be hand-written.
- Flask: workable, but needs extra libraries for validation.
