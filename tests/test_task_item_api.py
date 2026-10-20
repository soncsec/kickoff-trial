import pytest
from fastapi.testclient import TestClient

from kickoff_trial.main import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "tasks.db"))


@pytest.fixture
def task(client):
    return client.post("/tasks", json={"title": "Buy milk"}).json()


def test_get_returns_the_task(client, task):
    response = client.get(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json() == task


def test_get_missing_returns_404(client):
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_get_with_non_integer_id_returns_422(client):
    assert client.get("/tasks/abc").status_code == 422


def test_patch_done_marks_task_done(client, task):
    response = client.patch(f"/tasks/{task['id']}", json={"done": True})

    assert response.status_code == 200
    assert response.json() == {**task, "done": True}
    assert client.get(f"/tasks/{task['id']}").json()["done"] is True


def test_patch_done_false_marks_task_not_done(client, task):
    client.patch(f"/tasks/{task['id']}", json={"done": True})

    response = client.patch(f"/tasks/{task['id']}", json={"done": False})

    assert response.status_code == 200
    assert response.json() == task


def test_patch_title_renames_task(client, task):
    response = client.patch(f"/tasks/{task['id']}", json={"title": "Buy oat milk"})

    assert response.status_code == 200
    assert response.json() == {**task, "title": "Buy oat milk"}
    assert client.get(f"/tasks/{task['id']}").json()["title"] == "Buy oat milk"


def test_patch_title_and_done_together(client, task):
    response = client.patch(f"/tasks/{task['id']}", json={"title": "Buy oat milk", "done": True})

    assert response.json() == {**task, "title": "Buy oat milk", "done": True}


def test_patch_title_of_200_characters_is_accepted(client, task):
    response = client.patch(f"/tasks/{task['id']}", json={"title": "x" * 200})

    assert response.status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "x" * 201},
        {"title": 42},
        {"title": None},
        {"done": "yes"},
        {"done": 1},
        {"done": None},
        {"done": True, "extra": "field"},
        {"id": 7},
    ],
    ids=[
        "empty-body",
        "empty-title",
        "too-long-title",
        "number-title",
        "null-title",
        "string-done",
        "number-done",
        "null-done",
        "extra-field",
        "id-field",
    ],
)
def test_invalid_patch_returns_422_and_changes_nothing(client, task, payload):
    response = client.patch(f"/tasks/{task['id']}", json=payload)

    assert response.status_code == 422
    assert client.get(f"/tasks/{task['id']}").json() == task


def test_patch_missing_returns_404(client):
    response = client.patch("/tasks/999", json={"done": True})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_patch_with_non_integer_id_returns_422(client):
    assert client.patch("/tasks/abc", json={"done": True}).status_code == 422
