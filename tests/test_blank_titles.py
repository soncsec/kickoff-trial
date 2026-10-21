import pytest
from fastapi.testclient import TestClient

from kickoff_trial.main import create_app

BLANK_TITLES = [" ", "   ", "\t", "\n", " \t\r\n ", " ", "　"]
BLANK_IDS = ["space", "spaces", "tab", "newline", "mixed", "no-break-space", "ideographic-space"]


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "tasks.db"))


@pytest.mark.parametrize("title", BLANK_TITLES, ids=BLANK_IDS)
def test_create_with_blank_title_returns_422_and_stores_nothing(client, title):
    response = client.post("/tasks", json={"title": title})

    assert response.status_code == 422
    assert client.get("/tasks").json() == []


@pytest.mark.parametrize("title", BLANK_TITLES, ids=BLANK_IDS)
def test_patch_with_blank_title_returns_422_and_changes_nothing(client, title):
    task = client.post("/tasks", json={"title": "Buy milk"}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"title": title})

    assert response.status_code == 422
    assert client.get(f"/tasks/{task['id']}").json() == task


def test_title_with_spaces_around_text_is_stored_exactly(client):
    response = client.post("/tasks", json={"title": "  Buy milk "})

    assert response.status_code == 201
    assert response.json()["title"] == "  Buy milk "
    assert client.get("/tasks").json()[0]["title"] == "  Buy milk "


def test_patch_title_with_spaces_around_text_is_stored_exactly(client):
    task = client.post("/tasks", json={"title": "Buy milk"}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"title": " Walk dog\t"})

    assert response.status_code == 200
    assert response.json()["title"] == " Walk dog\t"


def test_single_visible_character_is_accepted(client):
    assert client.post("/tasks", json={"title": "x"}).status_code == 201


def test_200_characters_with_surrounding_spaces_is_accepted(client):
    assert client.post("/tasks", json={"title": " " + "x" * 198 + " "}).status_code == 201


def test_201_characters_is_still_rejected(client):
    assert client.post("/tasks", json={"title": " " + "x" * 200}).status_code == 422
