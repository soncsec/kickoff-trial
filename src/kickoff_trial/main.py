"""The HTTP API: `create_app()` builds the FastAPI application."""

from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Self

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kickoff_trial.storage import TaskStore, db_path

Title = Annotated[str, Field(min_length=1, max_length=200)]


class TaskCreate(BaseModel):
    """What a client sends to create a task. Unknown fields are rejected (threat model T4)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: Title


class TaskUpdate(BaseModel):
    """What a client sends to change a task: at least one field, and no nulls."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: Title | None = None
    done: bool | None = None

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("send at least one of: title, done")
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


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

    @app.get("/tasks/{task_id}")
    def get_task(task_id: int) -> TaskOut:
        found = store.get(task_id)
        if found is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        return TaskOut(**asdict(found))

    @app.patch("/tasks/{task_id}")
    def update_task(task_id: int, changes: TaskUpdate) -> TaskOut:
        updated = store.update(task_id, title=changes.title, done=changes.done)
        if updated is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        return TaskOut(**asdict(updated))

    @app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(task_id: int) -> None:
        if not store.delete(task_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    return app
