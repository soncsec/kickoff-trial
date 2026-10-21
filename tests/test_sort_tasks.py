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


def test_sort_newest_lists_newest_first(client, tasks):
    response = client.get("/tasks", params={"sort": "newest"})

    assert response.status_code == 200
    assert response.json() == list(reversed(tasks))


def test_sort_oldest_lists_oldest_first(client, tasks):
    response = client.get("/tasks", params={"sort": "oldest"})

    assert response.status_code == 200
    assert response.json() == tasks


def test_no_sort_lists_oldest_first(client, tasks):
    assert client.get("/tasks").json() == tasks


@pytest.mark.parametrize(
    "value", ["", "Newest", "created_at", "-created_at", "id DESC", "newest; DROP TABLE tasks"]
)
def test_other_sort_values_return_422(client, tasks, value):
    assert client.get("/tasks", params={"sort": value}).status_code == 422
    assert client.get("/tasks").json() == tasks


def test_sort_works_with_done_filter(client, tasks):
    open_newest = client.get("/tasks", params={"done": "false", "sort": "newest"}).json()
    done_newest = client.get("/tasks", params={"done": "true", "sort": "newest"}).json()

    assert open_newest == [tasks[2], tasks[0]]
    assert done_newest == [tasks[3], tasks[1]]


def test_store_lists_newest_first(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    first, second, third = store.add("a"), store.add("b"), store.add("c")

    assert store.list(newest=True) == [third, second, first]
    assert store.list(newest=False) == [first, second, third]
    assert store.list(done=False, newest=True) == [third, second, first]
