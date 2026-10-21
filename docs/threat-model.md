# Threat model

Last reviewed: 2026-10-21. Review it whenever a change touches sign-in,
sensitive data, untrusted input, secrets or a new dependency (issues labeled
`security`).

## What we protect

| Asset | Why it matters | Sensitivity |
| --- | --- | --- |
| Task list (`todo.db`) | The operator's tasks; losing or corrupting them is annoying | None sensitive |
| The operator's machine | The server runs there with the operator's permissions | High |

## Entry points

- The HTTP API on `127.0.0.1` (JSON request bodies and path parameters), on the
  operator's machine or published on a server's localhost from the container.
- The `TODO_DB_PATH` setting, set by the operator.
- Dependencies (FastAPI, uvicorn and what they pull in).

## Trust boundaries

- Local HTTP client to the API: anything on this machine, including a web page
  in the operator's browser, can send requests.
- API to the SQLite file: request data becomes SQL parameters.

## Threats

Categories (STRIDE): Spoofing, Tampering, Repudiation, Information disclosure,
Denial of service, Elevation of privilege.

| # | Threat | Category | Mitigation | Status |
| --- | --- | --- | --- | --- |
| T1 | A remote machine reaches the API | Spoofing | `make run` binds `127.0.0.1` (ADR 0004). The container listens on `0.0.0.0` inside, and each server publishes its port on `127.0.0.1` only, with no reverse proxy (ADR 0007) | Mitigated locally; on servers it depends on the deploy setup, outside this repository |
| T2 | A malicious web page in the operator's browser sends requests to the API (cross-site requests, DNS rebinding) | Spoofing, Tampering | None | Accepted: the operator chose to live with it because the data is not sensitive and nothing runs on its behalf beyond editing tasks |
| T3 | A task title injects SQL | Tampering, Elevation of privilege | Every statement is parameterised; a test stores a title containing SQL and reads it back unchanged | Mitigated |
| T4 | Huge or malformed input fills the disk or crashes the server | Denial of service | Pydantic models reject unknown shapes and titles over 200 characters with `422`; tests cover it | Mitigated |
| T5 | Errors leak stack traces or file paths | Information disclosure | FastAPI returns a generic `500`; debug mode is never turned on | Mitigated |
| T6 | No record of who changed or deleted a task | Repudiation | None | Accepted: one user on their own machine, data not sensitive |
| T7 | Other local accounts read or edit `todo.db` | Information disclosure, Tampering | None beyond normal file permissions | Accepted: the operator's own machine, data not sensitive |
| T8 | A flaw in the app is used to take over the server | Elevation of privilege | The image runs as unprivileged user 10001 on a read-only filesystem, writing only to `/data` and `/tmp` | Mitigated |
| T9 | Other processes or users on a server use the API | Spoofing, Tampering | None | Accepted: the operator chose server-local access with no sign-in (ADR 0007); public exposure waits for sign-in |

Status is one of: **Mitigated** (in place and tested), **Planned #<issue>** (an
issue labeled `security` tracks it), or **Accepted** (the operator chose to live
with it; say why).

T3 is tested in `tests/test_storage.py` and T4 in `tests/test_tasks_api.py`.

## Covered by the harness

These need no rows above:

- Secrets are kept out of commits (gitleaks in CI), and agents cannot read them.
- Dependencies are locked, scanned for known vulnerabilities, and new releases
  are held back for 7 days.
- Code is scanned by Semgrep on every pull request; error-level findings block
  the merge.
- Agents cannot change their own guardrails, merge pull requests or deploy.
