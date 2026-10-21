# 0006. Due dates: date only, column added on startup

- Status: Accepted
- Date: 2026-10-20
- Decided by: the operator, while planning milestone M3

## Context

Milestone M3 gives tasks an optional due date and a way to list overdue tasks.
That changes the data model and the public API, and existing `todo.db` files
must keep working. ADR 0003 chose plain `sqlite3` with no migration tool.

## Decision

- A due date is a calendar date only (`YYYY-MM-DD`), with no time or time zone.
  It is stored as ISO text in a nullable `due_date` column.
- A task is overdue when it is not done and its due date is before today in the
  server's local time zone. A task due today is not overdue.
- When the store opens a database without the column, it adds it once with
  `ALTER TABLE tasks ADD COLUMN due_date TEXT`. Existing tasks get no due date.
- Clients send `due_date` on create and update; `"due_date": null` in a `PATCH`
  clears it (a `null` title or done is still rejected).
- Overdue tasks are listed with `GET /tasks?overdue=true`, a filter that
  combines with `done` and `sort`.

## Consequences

Simple to type and to compare, with no time zone handling in the data. Old
databases upgrade themselves with no extra tooling. If more schema changes
follow, the one-off column check should give way to a small versioned
migration step (a new ADR).

## Alternatives considered

- Date and time in UTC: more precise, but fiddly to type and needs time zone
  rules for "overdue".
- A migration tool or versioned schema table: more structure than one column needs.
- Starting fresh (delete `todo.db`): loses the operator's tasks.
- A separate `GET /tasks/overdue` endpoint: a second way to list tasks instead
  of one filter that combines with the others.
- Due dates that cannot be removed: forces a made-up date when plans change.
