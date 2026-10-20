# 0003. SQLite through the standard library's sqlite3

- Status: Accepted
- Date: 2026-10-20
- Decided by: the operator, during kickoff

## Context

Tasks should survive a server restart. There is one user and one process.

## Decision

Store tasks in a single SQLite file, accessed with Python's built-in `sqlite3`
module and parameterised SQL in a small storage module. The table is created
on startup if it does not exist.

## Consequences

No database server and no extra dependency. There is no migration tool, so a
schema change needs care; revisit if the schema starts changing often or a
second writer appears.

## Alternatives considered

- In memory only: simpler, but tasks are lost on restart.
- PostgreSQL: built for many writers; needs a running server for no benefit here.
- SQLModel or SQLAlchemy: an ORM and migrations are more than one table needs.
