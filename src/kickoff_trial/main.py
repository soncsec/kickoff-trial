"""The HTTP API: `create_app()` builds the FastAPI application."""

from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, status
from pydantic import BaseModel, ConfigDict, Field

from kickoff_trial.storage import TaskStore, db_path

Title = Annotated[str, Field(min_length=1, max_length=200)]


class TaskCreate(BaseModel):
    """What a client sends to create a task. Unknown fields are rejected (threat model T4)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: Title


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool
    created_at: str


def create_app(database: Path | str | None = None) -> FastAPI:
    """Build the app. `database` defaults to the `TODO_DB_PATH` setting; tests pass a temp file."""
    store = TaskStore(database if database is not None else db_path())
    app = FastAPI(title="kickoff-trial")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/tasks", status_code=status.HTTP_201_CREATED)
    def create_task(task: TaskCreate) -> TaskOut:
        return TaskOut(**asdict(store.add(task.title)))

    @app.get("/tasks")
    def list_tasks() -> list[TaskOut]:
        return [TaskOut(**asdict(t)) for t in store.list()]

    return app
