import pytest
from fastapi.testclient import TestClient

from kickoff_trial.main import create_app


@pytest.fixture
def db_file(tmp_path):
    return tmp_path / "tasks.db"


@pytest.fixture
def client(db_file):
    return TestClient(create_app(db_file))


def test_create_task_returns_201_and_the_task(client):
    response = client.post("/tasks", json={"title": "Buy milk"})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "title", "done", "created_at"}
    assert isinstance(body["id"], int)
    assert body["title"] == "Buy milk"
    assert body["done"] is False
    assert body["created_at"]


def test_list_is_empty_at_first(client):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_tasks_oldest_first(client):
    created = [client.post("/tasks", json={"title": t}).json() for t in ("one", "two", "three")]

    assert client.get("/tasks").json() == created


def test_title_of_200_characters_is_accepted(client):
    response = client.post("/tasks", json={"title": "x" * 200})

    assert response.status_code == 201


@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {"title": "x" * 201},
        {},
        {"title": "Buy milk", "done": True},
        {"title": "Buy milk", "extra": "field"},
        {"title": 42},
        {"title": None},
    ],
    ids=["empty", "too-long", "missing", "extra-done", "extra-field", "number", "null"],
)
def test_invalid_input_returns_422_and_stores_nothing(client, payload):
    response = client.post("/tasks", json=payload)

    assert response.status_code == 422
    assert client.get("/tasks").json() == []


def test_body_that_is_not_json_returns_422(client):
    response = client.post(
        "/tasks", content="title=Buy milk", headers={"content-type": "text/plain"}
    )

    assert response.status_code == 422
    assert client.get("/tasks").json() == []


def test_task_is_still_listed_after_app_is_recreated(db_file):
    created = TestClient(create_app(db_file)).post("/tasks", json={"title": "Buy milk"}).json()

    assert TestClient(create_app(db_file)).get("/tasks").json() == [created]
