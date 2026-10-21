"""Task storage in a local SQLite file.

Every statement uses `?` parameters: request data is never put into SQL text
(threat model T3). Each call opens its own short-lived connection, so the store
is safe to use from FastAPI's thread pool.
"""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum
from pathlib import Path

DEFAULT_DB_PATH = "todo.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    due_date TEXT
)
"""
# Databases created before due dates existed get the column once, on startup (ADR 0006).
_ADD_DUE_DATE = "ALTER TABLE tasks ADD COLUMN due_date TEXT"

_LIST_OLDEST_FIRST = (
    "SELECT id, title, done, created_at, due_date FROM tasks"
    " WHERE (? IS NULL OR done = ?) ORDER BY id"
)
_LIST_NEWEST_FIRST = (
    "SELECT id, title, done, created_at, due_date FROM tasks"
    " WHERE (? IS NULL OR done = ?) ORDER BY id DESC"
)


class _Unset(Enum):
    """Marks an `update` argument that was not given, as opposed to `None` (clear it)."""

    UNSET = "unset"


UNSET = _Unset.UNSET


def db_path() -> Path:
    """The database file: the `TODO_DB_PATH` setting, or `todo.db`."""
    return Path(os.environ.get("TODO_DB_PATH", DEFAULT_DB_PATH))


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    done: bool
    created_at: str
    due_date: date | None = None


def _to_task(row: sqlite3.Row) -> Task:
    due = row["due_date"]
    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
        created_at=row["created_at"],
        due_date=date.fromisoformat(due) if due is not None else None,
    )


def _iso(day: date | None) -> str | None:
    return day.isoformat() if day is not None else None


class TaskStore:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        with self._connect() as conn:
            conn.execute(_SCHEMA)
            names = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
            if "due_date" not in names:
                conn.execute(_ADD_DUE_DATE)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """A connection that commits on success, rolls back on error, and always closes."""
        with closing(sqlite3.connect(self._path)) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                yield conn

    def add(self, title: str, *, due_date: date | None = None) -> Task:
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "INSERT INTO tasks (title, done, created_at, due_date) VALUES (?, 0, ?, ?)"
                " RETURNING id, title, done, created_at, due_date",
                (title, created_at, _iso(due_date)),
            ).fetchone()
        return _to_task(row)

    def list(self, *, done: bool | None = None, newest: bool = False) -> list[Task]:
        """All tasks, or only those whose `done` matches; oldest first unless `newest`.

        The order picks one of two fixed statements, so no caller text reaches the SQL.
        Ids grow with creation, so ordering by id is ordering by creation time.
        """
        flag = None if done is None else int(done)
        sql = _LIST_NEWEST_FIRST if newest else _LIST_OLDEST_FIRST
        with self._connect() as conn:
            rows = conn.execute(sql, (flag, flag)).fetchall()
        return [_to_task(row) for row in rows]

    def get(self, task_id: int) -> Task | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, title, done, created_at, due_date FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return _to_task(row) if row else None

    def update(
        self,
        task_id: int,
        *,
        title: str | None = None,
        done: bool | None = None,
        due_date: date | None | _Unset = UNSET,
    ) -> Task | None:
        """Change the given fields.

        `None` leaves `title` and `done` as they are. `due_date` is left alone unless
        given; `None` clears it.
        """
        change_due = not isinstance(due_date, _Unset)
        new_due = _iso(due_date) if change_due else None
        with self._connect() as conn:
            row = conn.execute(
                "UPDATE tasks SET title = COALESCE(?, title), done = COALESCE(?, done),"
                " due_date = CASE WHEN ? THEN ? ELSE due_date END"
                " WHERE id = ? RETURNING id, title, done, created_at, due_date",
                (title, None if done is None else int(done), int(change_due), new_due, task_id),
            ).fetchone()
        return _to_task(row) if row else None

    def delete(self, task_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0
