import pytest
from fastapi.testclient import TestClient

from kickoff_trial.main import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "tasks.db"))


def add(client, title):
    return client.post("/tasks", json={"title": title}).json()


def test_delete_returns_204_with_empty_body(client):
    task = add(client, "Buy milk")

    response = client.delete(f"/tasks/{task['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_deleted_task_is_gone(client):
    task = add(client, "Buy milk")

    client.delete(f"/tasks/{task['id']}")

    assert client.get("/tasks").json() == []
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_delete_leaves_other_tasks(client):
    first = add(client, "Buy milk")
    second = add(client, "Walk dog")

    client.delete(f"/tasks/{first['id']}")

    assert client.get("/tasks").json() == [second]


def test_deleting_twice_returns_404_the_second_time(client):
    task = add(client, "Buy milk")
    client.delete(f"/tasks/{task['id']}")

    response = client.delete(f"/tasks/{task['id']}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_delete_missing_returns_404(client):
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_delete_with_non_integer_id_returns_422(client):
    task = add(client, "Buy milk")

    assert client.delete("/tasks/abc").status_code == 422
    assert client.get("/tasks").json() == [task]
