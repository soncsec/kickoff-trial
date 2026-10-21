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

One table of tasks: id, title (1–200 characters), done flag, created time, and an
optional due date (a calendar date; see [ADR 0006](adr/0006-due-dates.md)).
It lives in a SQLite file whose path comes from the `TODO_DB_PATH` setting
(default `todo.db` in the working directory, ignored by git). Tasks are kept
until deleted. Nothing in it is sensitive.

## Interfaces

| Method and path | What it does |
| --- | --- |
| `GET /health` | Returns `{"status": "ok"}` |
| `POST /tasks` | Creates a task from `{"title": "...", "due_date": "YYYY-MM-DD"}` (`due_date` optional); returns it with `201` |
| `GET /tasks` | Lists all tasks, oldest first; `?done=true` or `?done=false` lists only done or open tasks; `?sort=newest` lists newest first (`oldest` is the default) |
| `GET /tasks/{id}` | Returns one task, or `404` |
| `PATCH /tasks/{id}` | Updates `title`, `done` and/or `due_date` (`"due_date": null` clears it); returns the task, or `404` |
| `DELETE /tasks/{id}` | Deletes a task; `204`, or `404` |

Every task in a response has `id`, `title`, `done`, `created_at` and `due_date`
(a `YYYY-MM-DD` string or `null`). A due date must be a real calendar date in
exactly that form. Invalid input gets `422` with FastAPI's standard error body.

## Security boundaries

Untrusted input enters only through the HTTP API, which is reachable from
localhost only: `make run` binds `127.0.0.1`, and a deployed container is
published on the server's `127.0.0.1` (ADR 0007). There is no sign-in: anyone
who can reach localhost on that machine is trusted.
Input is validated by Pydantic models, and every SQL statement is
parameterised. There are no secrets. The details are in the
[threat model](threat-model.md).

## Environments

- **Local:** `make run` starts the server on `127.0.0.1`.
- **CI:** `make check` (lint, tests, scans) runs on every pull request.
- **Container image:** `make container-context` writes `dist/*.whl` and a
  hashed `requirements.txt`; the `Containerfile` installs them and runs uvicorn
  on `0.0.0.0:$PORT` as an unprivileged user, with the database at
  `/data/todo.db` in the writable `/data` volume.
- **Servers:** the harness deploy path ships the image. Each server publishes the
  port on `127.0.0.1` only, with no reverse proxy, so only the server itself can
  reach the app ([ADR 0007](adr/0007-container-deploy-without-public-exposure.md)).

## Testing

Unit tests for the storage module, tests through the HTTP interface with
FastAPI's test client, and the checks CI runs on every pull request
(`make check`). Each test gets its own temporary SQLite file.

## Decisions

Each significant choice has an ADR in [docs/adr/](adr/), with the alternatives
considered.
