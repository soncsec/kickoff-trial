import sqlite3

import pytest

from kickoff_trial.storage import Task, TaskStore, db_path


@pytest.fixture
def db_file(tmp_path):
    return tmp_path / "tasks.db"


@pytest.fixture
def store(db_file):
    return TaskStore(db_file)


def table_names(path):
    with sqlite3.connect(path) as conn:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def test_creates_tasks_table(db_file):
    TaskStore(db_file)

    assert "tasks" in table_names(db_file)


def test_creating_store_twice_keeps_existing_tasks(db_file):
    TaskStore(db_file).add("Buy milk")

    assert [t.title for t in TaskStore(db_file).list()] == ["Buy milk"]


def test_add_returns_new_task(store):
    task = store.add("Buy milk")

    assert isinstance(task, Task)
    assert task.id > 0
    assert task.title == "Buy milk"
    assert task.done is False
    assert task.created_at


def test_list_is_empty_at_first(store):
    assert store.list() == []


def test_list_returns_tasks_oldest_first(store):
    first = store.add("first")
    second = store.add("second")
    third = store.add("third")

    assert store.list() == [first, second, third]


def test_get_returns_task(store):
    task = store.add("Buy milk")

    assert store.get(task.id) == task


def test_get_missing_returns_none(store):
    assert store.get(999) is None


def test_update_done(store):
    task = store.add("Buy milk")

    updated = store.update(task.id, done=True)

    assert updated is not None
    assert updated.done is True
    assert updated.title == "Buy milk"
    assert store.get(task.id) == updated


def test_update_title(store):
    task = store.add("Buy milk")

    updated = store.update(task.id, title="Buy oat milk")

    assert updated is not None
    assert updated.title == "Buy oat milk"
    assert updated.done is False
    assert store.get(task.id) == updated


def test_update_with_nothing_leaves_task_unchanged(store):
    task = store.add("Buy milk")

    assert store.update(task.id) == task


def test_update_missing_returns_none(store):
    assert store.update(999, done=True) is None


def test_delete_removes_task(store):
    task = store.add("Buy milk")
    other = store.add("Walk dog")

    assert store.delete(task.id) is True
    assert store.get(task.id) is None
    assert store.list() == [other]


def test_delete_missing_returns_false(store):
    assert store.delete(999) is False


def test_sql_in_title_is_stored_as_text(store, db_file):
    title = "'); DROP TABLE tasks; --"

    task = store.add(title)
    store.update(task.id, title=title)

    assert store.get(task.id).title == title
    assert "tasks" in table_names(db_file)
    assert [t.title for t in store.list()] == [title]


def test_db_path_defaults_to_todo_db(monkeypatch):
    monkeypatch.delenv("TODO_DB_PATH", raising=False)

    assert str(db_path()) == "todo.db"


def test_db_path_comes_from_setting(monkeypatch, tmp_path):
    monkeypatch.setenv("TODO_DB_PATH", str(tmp_path / "mine.db"))

    assert db_path() == tmp_path / "mine.db"
