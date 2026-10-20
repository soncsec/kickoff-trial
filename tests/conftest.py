import pytest


@pytest.fixture(autouse=True)
def isolated_db_path(tmp_path, monkeypatch):
    """Point the default database at a temp file, so no test writes todo.db in the repo."""
    monkeypatch.setenv("TODO_DB_PATH", str(tmp_path / "default.db"))
