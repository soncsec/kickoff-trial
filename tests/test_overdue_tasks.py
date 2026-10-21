from datetime import date

import pytest
from fastapi.testclient import TestClient

from kickoff_trial.main import create_app
from kickoff_trial.storage import TaskStore

TODAY = date(2026, 10, 21)


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "tasks.db", today=lambda: TODAY))


@pytest.fixture
def tasks(client):
    """Tasks in creation order, named for how they relate to TODAY."""

    def add(title, due=None, done=False):
        task = client.post("/tasks", json={"title": title, "due_date": due}).json()
        if done:
            task = client.patch(f"/tasks/{task['id']}", json={"done": True}).json()
        return task

    return {
        "overdue_old": add("overdue old", "2026-09-01"),
        "due_today": add("due today", "2026-10-21"),
        "no_due": add("no due date"),
        "done_past": add("done, was due", "2026-10-01", done=True),
        "future": add("due later", "2026-12-24"),
        "overdue_yesterday": add("overdue yesterday", "2026-10-20"),
    }


def titles(response):
    return [t["title"] for t in response.json()]


def test_overdue_true_lists_open_tasks_due_before_today(client, tasks):
    response = client.get("/tasks", params={"overdue": "true"})

    assert response.status_code == 200
    assert response.json() == [tasks["overdue_old"], tasks["overdue_yesterday"]]


def test_task_due_today_is_not_overdue(client, tasks):
    assert "due today" not in titles(client.get("/tasks", params={"overdue": "true"}))


def test_overdue_false_lists_every_task_that_is_not_overdue(client, tasks):
    response = client.get("/tasks", params={"overdue": "false"})

    assert response.json() == [
        tasks["due_today"],
        tasks["no_due"],
        tasks["done_past"],
        tasks["future"],
    ]


def test_no_overdue_parameter_lists_all_tasks(client, tasks):
    assert client.get("/tasks").json() == list(tasks.values())


@pytest.mark.parametrize("value", ["", "yes", "1", "True", "overdue"])
def test_other_overdue_values_return_422(client, tasks, value):
    assert client.get("/tasks", params={"overdue": value}).status_code == 422


def test_overdue_with_sort_newest(client, tasks):
    response = client.get("/tasks", params={"overdue": "true", "sort": "newest"})

    assert response.json() == [tasks["overdue_yesterday"], tasks["overdue_old"]]


def test_overdue_with_done(client, tasks):
    assert client.get("/tasks", params={"overdue": "true", "done": "true"}).json() == []
    assert client.get("/tasks", params={"overdue": "false", "done": "true"}).json() == [
        tasks["done_past"]
    ]
    assert client.get("/tasks", params={"overdue": "true", "done": "false"}).json() == [
        tasks["overdue_old"],
        tasks["overdue_yesterday"],
    ]


def test_marking_overdue_task_done_removes_it(client, tasks):
    client.patch(f"/tasks/{tasks['overdue_old']['id']}", json={"done": True})

    assert titles(client.get("/tasks", params={"overdue": "true"})) == ["overdue yesterday"]


def test_today_is_read_on_each_request(tmp_path):
    days = iter([date(2026, 10, 24), date(2026, 10, 26)])
    client = TestClient(create_app(tmp_path / "tasks.db", today=lambda: next(days)))
    client.post("/tasks", json={"title": "due 25th", "due_date": "2026-10-25"})

    assert client.get("/tasks", params={"overdue": "true"}).json() == []
    assert titles(client.get("/tasks", params={"overdue": "true"})) == ["due 25th"]


def test_default_today_is_local_date(tmp_path, monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 10, 21)

    monkeypatch.setattr("kickoff_trial.main.date", FixedDate)
    client = TestClient(create_app(tmp_path / "tasks.db"))
    client.post("/tasks", json={"title": "yesterday", "due_date": "2026-10-20"})
    client.post("/tasks", json={"title": "today", "due_date": "2026-10-21"})

    assert titles(client.get("/tasks", params={"overdue": "true"})) == ["yesterday"]


def test_store_filters_overdue(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    late = store.add("late", due_date=date(2026, 10, 1))
    on_time = store.add("on time", due_date=TODAY)
    undated = store.add("undated")

    assert store.list(overdue=True, today=TODAY) == [late]
    assert store.list(overdue=False, today=TODAY) == [on_time, undated]
    assert store.list() == [late, on_time, undated]


def test_store_needs_today_to_filter_overdue(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")

    with pytest.raises(ValueError, match="today"):
        store.list(overdue=True)
