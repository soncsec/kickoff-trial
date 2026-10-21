import sqlite3
from datetime import date

import pytest

from kickoff_trial.storage import TaskStore

OLD_SCHEMA = """
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
)
"""


@pytest.fixture
def db_file(tmp_path):
    return tmp_path / "tasks.db"


@pytest.fixture
def store(db_file):
    return TaskStore(db_file)


def columns(path):
    with sqlite3.connect(path) as conn:
        return [row[1] for row in conn.execute("PRAGMA table_info(tasks)")]


def make_old_database(path):
    with sqlite3.connect(path) as conn:
        conn.execute(OLD_SCHEMA)
        conn.execute(
            "INSERT INTO tasks (title, done, created_at) VALUES (?, ?, ?)",
            ("old task", 1, "2026-10-01T09:00:00+00:00"),
        )


def test_new_database_has_nullable_due_date_column(db_file):
    TaskStore(db_file)

    with sqlite3.connect(db_file) as conn:
        info = {row[1]: row for row in conn.execute("PRAGMA table_info(tasks)")}
    assert "due_date" in info
    assert info["due_date"][2] == "TEXT"
    assert info["due_date"][3] == 0  # not NOT NULL


def test_old_database_gets_column_and_keeps_tasks(db_file):
    make_old_database(db_file)

    store = TaskStore(db_file)

    assert "due_date" in columns(db_file)
    [task] = store.list()
    assert task.title == "old task"
    assert task.done is True
    assert task.created_at == "2026-10-01T09:00:00+00:00"
    assert task.due_date is None


def test_opening_upgraded_database_again_changes_nothing(db_file):
    make_old_database(db_file)
    TaskStore(db_file).add("new task", due_date=date(2026, 10, 25))
    before = TaskStore(db_file).list()

    after = TaskStore(db_file).list()

    assert after == before
    assert columns(db_file).count("due_date") == 1


def test_add_without_due_date_has_none(store):
    assert store.add("Buy milk").due_date is None


def test_add_with_due_date(store):
    task = store.add("Buy milk", due_date=date(2026, 10, 25))

    assert task.due_date == date(2026, 10, 25)
    assert store.get(task.id).due_date == date(2026, 10, 25)


def test_due_date_is_stored_as_iso_text(store, db_file):
    task = store.add("Buy milk", due_date=date(2026, 1, 5))

    with sqlite3.connect(db_file) as conn:
        [stored] = conn.execute("SELECT due_date FROM tasks WHERE id = ?", (task.id,)).fetchone()
    assert stored == "2026-01-05"


def test_update_sets_due_date(store):
    task = store.add("Buy milk")

    updated = store.update(task.id, due_date=date(2026, 10, 25))

    assert updated.due_date == date(2026, 10, 25)
    assert store.get(task.id).due_date == date(2026, 10, 25)


def test_update_changes_due_date(store):
    task = store.add("Buy milk", due_date=date(2026, 10, 25))

    assert store.update(task.id, due_date=date(2026, 11, 1)).due_date == date(2026, 11, 1)


def test_update_clears_due_date_with_none(store):
    task = store.add("Buy milk", due_date=date(2026, 10, 25))

    updated = store.update(task.id, due_date=None)

    assert updated.due_date is None
    assert store.get(task.id).due_date is None


def test_update_without_due_date_leaves_it_alone(store):
    task = store.add("Buy milk", due_date=date(2026, 10, 25))

    updated = store.update(task.id, title="Buy oat milk", done=True)

    assert updated.due_date == date(2026, 10, 25)


def test_list_includes_due_dates(store):
    first = store.add("a", due_date=date(2026, 10, 25))
    second = store.add("b")

    assert store.list() == [first, second]
    assert [t.due_date for t in store.list(newest=True)] == [None, date(2026, 10, 25)]
