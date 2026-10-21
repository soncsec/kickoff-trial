import pytest
from fastapi.testclient import TestClient

from kickoff_trial.main import create_app

BAD_DATES = [
    "2026-02-30",
    "2026-13-01",
    "25/10/2026",
    "2026-10-25T10:00",
    "2026-10-25T00:00:00",
    "20261025",
    "2026-1-5",
    " 2026-10-25",
    "",
    "tomorrow",
    20261025,
    True,
    ["2026-10-25"],
]
BAD_IDS = [
    "feb-30",
    "month-13",
    "day-first",
    "with-time",
    "midnight",
    "no-dashes",
    "no-padding",
    "leading-space",
    "empty",
    "word",
    "number",
    "bool",
    "list",
]


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "tasks.db"))


def test_created_task_without_due_date_has_null(client):
    body = client.post("/tasks", json={"title": "Buy milk"}).json()

    assert body["due_date"] is None


def test_create_with_due_date(client):
    response = client.post("/tasks", json={"title": "Buy milk", "due_date": "2026-10-25"})

    assert response.status_code == 201
    assert response.json()["due_date"] == "2026-10-25"
    assert client.get(f"/tasks/{response.json()['id']}").json()["due_date"] == "2026-10-25"


def test_create_with_null_due_date_is_allowed(client):
    response = client.post("/tasks", json={"title": "Buy milk", "due_date": None})

    assert response.status_code == 201
    assert response.json()["due_date"] is None


def test_leap_day_is_accepted(client):
    response = client.post("/tasks", json={"title": "Buy milk", "due_date": "2028-02-29"})

    assert response.status_code == 201


def test_every_listed_task_has_due_date(client):
    client.post("/tasks", json={"title": "a", "due_date": "2026-10-25"})
    client.post("/tasks", json={"title": "b"})

    assert [t["due_date"] for t in client.get("/tasks").json()] == ["2026-10-25", None]


@pytest.mark.parametrize("value", BAD_DATES, ids=BAD_IDS)
def test_create_with_bad_due_date_returns_422_and_stores_nothing(client, value):
    response = client.post("/tasks", json={"title": "Buy milk", "due_date": value})

    assert response.status_code == 422
    assert client.get("/tasks").json() == []


def test_patch_sets_due_date(client):
    task = client.post("/tasks", json={"title": "Buy milk"}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"due_date": "2026-10-25"})

    assert response.status_code == 200
    assert response.json() == {**task, "due_date": "2026-10-25"}


def test_patch_changes_due_date(client):
    task = client.post("/tasks", json={"title": "Buy milk", "due_date": "2026-10-25"}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"due_date": "2026-11-01"})

    assert response.json()["due_date"] == "2026-11-01"


def test_patch_null_clears_due_date(client):
    task = client.post("/tasks", json={"title": "Buy milk", "due_date": "2026-10-25"}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"due_date": None})

    assert response.status_code == 200
    assert response.json() == {**task, "due_date": None}
    assert client.get(f"/tasks/{task['id']}").json()["due_date"] is None


def test_patch_other_fields_keeps_due_date(client):
    task = client.post("/tasks", json={"title": "Buy milk", "due_date": "2026-10-25"}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"done": True, "title": "Buy oat milk"})

    assert response.json()["due_date"] == "2026-10-25"


def test_patch_with_only_due_date_is_not_empty(client):
    task = client.post("/tasks", json={"title": "Buy milk"}).json()

    assert client.patch(f"/tasks/{task['id']}", json={"due_date": None}).status_code == 200


@pytest.mark.parametrize(
    "payload", [{"title": None}, {"done": None}, {"title": None, "due_date": None}]
)
def test_patch_null_title_or_done_still_returns_422(client, payload):
    task = client.post("/tasks", json={"title": "Buy milk", "due_date": "2026-10-25"}).json()

    assert client.patch(f"/tasks/{task['id']}", json=payload).status_code == 422
    assert client.get(f"/tasks/{task['id']}").json() == task


@pytest.mark.parametrize("value", BAD_DATES, ids=BAD_IDS)
def test_patch_with_bad_due_date_returns_422_and_changes_nothing(client, value):
    task = client.post("/tasks", json={"title": "Buy milk", "due_date": "2026-10-25"}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"due_date": value})

    assert response.status_code == 422
    assert client.get(f"/tasks/{task['id']}").json() == task


def test_patch_due_date_on_missing_task_returns_404(client):
    assert client.patch("/tasks/999", json={"due_date": "2026-10-25"}).status_code == 404
