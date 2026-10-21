"""The container image definition matches what the deploy path expects (ADR 0007)."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONTAINERFILE = ROOT / "Containerfile"


@pytest.fixture
def instructions():
    """Containerfile instructions as (keyword, arguments), with continuation lines joined."""
    text = re.sub(r"\\\n", " ", CONTAINERFILE.read_text())
    lines = [line.strip() for line in text.splitlines()]
    return [tuple(line.split(None, 1)) for line in lines if line and not line.startswith("#")]


def env_values(instructions):
    values = {}
    for keyword, args in instructions:
        if keyword == "ENV":
            values.update(dict(pair.split("=", 1) for pair in args.split()))
    return values


def test_cmd_starts_the_app_on_all_interfaces_and_port_env(instructions):
    [cmd] = [args for keyword, args in instructions if keyword == "CMD"]
    command = json.loads(cmd)

    assert command[:2] == ["sh", "-c"]
    assert command[2] == (
        'exec uvicorn kickoff_trial.main:create_app --factory --host 0.0.0.0 --port "$PORT"'
    )


def test_database_lives_in_the_data_volume(instructions):
    assert env_values(instructions)["TODO_DB_PATH"] == "/data/todo.db"


def test_app_runs_as_unprivileged_user(instructions):
    [user] = [args for keyword, args in instructions if keyword == "USER"]

    assert user not in {"0", "root"}


def test_default_port_is_8000(instructions):
    assert env_values(instructions)["PORT"] == "8000"


def test_requirements_txt_is_git_ignored():
    ignored = (ROOT / ".gitignore").read_text().splitlines()

    assert "requirements.txt" in ignored or "/requirements.txt" in ignored


def test_makefile_has_container_context_target():
    makefile = (ROOT / "Makefile").read_text()

    assert re.search(r"^container-context:", makefile, re.MULTILINE)
