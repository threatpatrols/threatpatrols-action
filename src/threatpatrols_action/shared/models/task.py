from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from . import PrivateHandleBaseModel


class TaskState(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskListItemResponse(BaseModel):
    task_id: str
    state: TaskState


class TaskResponse(PrivateHandleBaseModel):
    task_id: str
    state: TaskState

    # model_config = ConfigDict(
    #     json_schema_extra={
    #         "example": {"task_id": "12345678", "state": "pending", "tags": {"request_id": "ff0e4d8113924be6-TPX"}}
    #     }
    # )
