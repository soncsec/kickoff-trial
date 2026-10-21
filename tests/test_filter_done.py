import pytest
from fastapi.testclient import TestClient

from kickoff_trial.main import create_app
from kickoff_trial.storage import TaskStore


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "tasks.db"))


@pytest.fixture
def tasks(client):
    """Four tasks, oldest first; the second and fourth are done."""
    created = [client.post("/tasks", json={"title": t}).json() for t in ("a", "b", "c", "d")]
    for task in (created[1], created[3]):
        task.update(client.patch(f"/tasks/{task['id']}", json={"done": True}).json())
    return created


def test_done_false_lists_only_open_tasks_oldest_first(client, tasks):
    response = client.get("/tasks", params={"done": "false"})

    assert response.status_code == 200
    assert response.json() == [tasks[0], tasks[2]]


def test_done_true_lists_only_done_tasks_oldest_first(client, tasks):
    response = client.get("/tasks", params={"done": "true"})

    assert response.status_code == 200
    assert response.json() == [tasks[1], tasks[3]]


def test_no_done_parameter_lists_all_tasks(client, tasks):
    assert client.get("/tasks").json() == tasks


def test_filter_with_no_matches_returns_empty_list(client):
    client.post("/tasks", json={"title": "open"})

    assert client.get("/tasks", params={"done": "true"}).json() == []


@pytest.mark.parametrize("value", ["maybe", "yes", "1", "0", "True", ""])
def test_other_done_values_return_422(client, tasks, value):
    assert client.get("/tasks", params={"done": value}).status_code == 422


def test_store_filters_by_done(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    first = store.add("a")
    second = store.update(store.add("b").id, done=True)
    third = store.add("c")

    assert store.list(done=False) == [first, third]
    assert store.list(done=True) == [second]
    assert store.list() == [first, second, third]
