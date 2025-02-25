import json
from enum import Enum

from pydantic import ConfigDict

from . import TASK_ITEM_EXAMPLE, TASK_ITEM_SUMMARY_EXAMPLE
from .base import BaseModelPrivateHandler


class TaskState(str, Enum):
    PENDING = "pending"
    ACTION_IN_PROGRESS = "action_in_progress"
    CALLBACKS_IN_PROGRESS = "callbacks_in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskItem(BaseModelPrivateHandler):
    task_id: str
    state: TaskState

    model_config = ConfigDict(extra="allow", json_schema_extra={"example": json.loads(TASK_ITEM_EXAMPLE)})


class TaskItemSummary(BaseModelPrivateHandler):
    task_id: str
    state: TaskState

    model_config = ConfigDict(extra="allow", json_schema_extra={"example": json.loads(TASK_ITEM_SUMMARY_EXAMPLE)})
