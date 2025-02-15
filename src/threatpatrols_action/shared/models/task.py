from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskState(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskListItemResponse(BaseModel):
    task_id: str
    state: TaskState


class TaskResponse(BaseModel):
    task_id: str
    state: TaskState
    tags: Optional[dict[str, str]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"task_id": "12345678", "state": "pending", "tags": {"request_id": "ff0e4d8113924be6-TPX"}}
        }
    )
