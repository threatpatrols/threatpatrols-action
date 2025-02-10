from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskState(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskResponse(BaseModel):
    task_id: str
    state: TaskState
    tags: Optional[dict[str, str]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "12345678",
                    "state": "pending",
                    "tags": {"request_id": "ff0e4d8113924be6-TPX"},
                }
            ]
        }
    )


class HealthResponse(BaseModel):
    status: str
    memory_usage: float
    cpu_usage: float

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "healthy", "memory_usage": 44.2, "cpu_usage": 14.3}]}
    )
