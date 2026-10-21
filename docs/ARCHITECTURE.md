# Architecture

kickoff-trial is a single-process HTTP API, written in Python with FastAPI,
that stores one user's to-do tasks in a local SQLite file. It runs on the
operator's machine and listens on localhost only.

## Components

```text
curl / script --HTTP, 127.0.0.1--> api (FastAPI, uvicorn) --sqlite3--> todo.db
```

| Component | What it does | Built with |
| --- | --- | --- |
| api | HTTP routes, request validation, JSON responses | FastAPI, Pydantic, uvicorn |
| storage | Creates the table and reads/writes tasks with parameterised SQL | Python's `sqlite3` |

The app is built by an app factory (`create_app()`), so tests can give it a
temporary database.

## Data

One table of tasks: id, title (1–200 characters), done flag, and created time.
It lives in a SQLite file whose path comes from the `TODO_DB_PATH` setting
(default `todo.db` in the working directory, ignored by git). Tasks are kept
until deleted. Nothing in it is sensitive.

## Interfaces

| Method and path | What it does |
| --- | --- |
| `GET /health` | Returns `{"status": "ok"}` |
| `POST /tasks` | Creates a task from `{"title": "..."}`; returns it with `201` |
| `GET /tasks` | Lists all tasks, oldest first; `?done=true` or `?done=false` lists only done or open tasks; `?sort=newest` lists newest first (`oldest` is the default) |
| `GET /tasks/{id}` | Returns one task, or `404` |
| `PATCH /tasks/{id}` | Updates `title` and/or `done`; returns the task, or `404` |
| `DELETE /tasks/{id}` | Deletes a task; `204`, or `404` |

Invalid input gets `422` with FastAPI's standard error body.

## Security boundaries

Untrusted input enters only through the HTTP API, which binds to `127.0.0.1`.
There is no sign-in: anyone who can reach localhost on this machine is trusted.
Input is validated by Pydantic models, and every SQL statement is
parameterised. There are no secrets. The details are in the
[threat model](threat-model.md).

## Environments

- **Local:** `make run` starts the server on `127.0.0.1`.
- **CI:** `make check` (lint, tests, scans) runs on every pull request.
- **Staging and production:** none; this project is not deployed.

## Testing

Unit tests for the storage module, tests through the HTTP interface with
FastAPI's test client, and the checks CI runs on every pull request
(`make check`). Each test gets its own temporary SQLite file.

## Decisions

Each significant choice has an ADR in [docs/adr/](adr/), with the alternatives
considered.
