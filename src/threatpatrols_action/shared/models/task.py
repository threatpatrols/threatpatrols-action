import json
from enum import StrEnum

from pydantic import ConfigDict

from . import TASK_ITEM_EXAMPLE, TASK_LIST_ITEM_EXAMPLE
from .base import BaseModelPrivateHandler


class TaskState(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskItem(BaseModelPrivateHandler):
    task_id: str
    state: TaskState

    model_config = ConfigDict(extra="allow", json_schema_extra={"example": json.loads(TASK_ITEM_EXAMPLE)})


class TaskListItem(BaseModelPrivateHandler):
    task_id: str
    state: TaskState

    model_config = ConfigDict(extra="allow", json_schema_extra={"example": json.loads(TASK_LIST_ITEM_EXAMPLE)})
