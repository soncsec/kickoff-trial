"""The HTTP API: `create_app()` builds the FastAPI application."""

import re
from collections.abc import Callable
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, Self

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from kickoff_trial.storage import UNSET, TaskStore, db_path


def _not_blank(title: str) -> str:
    """Reject titles with no visible characters; accepted titles are kept exactly as sent."""
    if not title.strip():
        raise ValueError("title must contain a visible character")
    return title


Title = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(_not_blank)]

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def _parse_due_date(value: object) -> object:
    """Accept only a real calendar date written as YYYY-MM-DD (ADR 0006)."""
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        raise ValueError("due_date must be a date written as YYYY-MM-DD")
    return date.fromisoformat(value)  # raises ValueError for dates like 2026-02-30


DueDate = Annotated[date, BeforeValidator(_parse_due_date)]


class TaskCreate(BaseModel):
    """What a client sends to create a task. Unknown fields are rejected (threat model T4)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: Title
    due_date: DueDate | None = None


class TaskUpdate(BaseModel):
    """What a client sends to change a task: at least one field.

    `"due_date": null` clears the due date; `null` for `title` or `done` is rejected.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    title: Title | None = None
    done: bool | None = None
    due_date: DueDate | None = None

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("send at least one of: title, done, due_date")
        for name in self.model_fields_set - {"due_date"}:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool
    created_at: str
    due_date: date | None


def _local_today() -> date:
    return date.today()


def create_app(
    database: Path | str | None = None, today: Callable[[], date] = _local_today
) -> FastAPI:
    """Build the app. `database` defaults to the `TODO_DB_PATH` setting; tests pass a temp file."""
    store = TaskStore(database if database is not None else db_path())
    app = FastAPI(title="kickoff-trial")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/tasks", status_code=status.HTTP_201_CREATED)
    def create_task(task: TaskCreate) -> TaskOut:
        return TaskOut(**asdict(store.add(task.title, due_date=task.due_date)))

    @app.get("/tasks")
    def list_tasks(
        # Exactly "true" or "false": FastAPI's bool would also accept yes, 1, on.
        done: Annotated[Literal["true", "false"] | None, Query()] = None,
        overdue: Annotated[Literal["true", "false"] | None, Query()] = None,
        sort: Annotated[Literal["oldest", "newest"], Query()] = "oldest",
    ) -> list[TaskOut]:
        flag = None if done is None else done == "true"
        late = None if overdue is None else overdue == "true"
        tasks = store.list(done=flag, overdue=late, today=today(), newest=sort == "newest")
        return [TaskOut(**asdict(t)) for t in tasks]

    @app.get("/tasks/{task_id}")
    def get_task(task_id: int) -> TaskOut:
        found = store.get(task_id)
        if found is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        return TaskOut(**asdict(found))

    @app.patch("/tasks/{task_id}")
    def update_task(task_id: int, changes: TaskUpdate) -> TaskOut:
        due = changes.due_date if "due_date" in changes.model_fields_set else UNSET
        updated = store.update(task_id, title=changes.title, done=changes.done, due_date=due)
        if updated is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        return TaskOut(**asdict(updated))

    @app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(task_id: int) -> None:
        if not store.delete(task_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    return app
