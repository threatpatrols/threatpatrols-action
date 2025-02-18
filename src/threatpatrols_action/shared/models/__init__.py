TASK_LIST_ITEM_EXAMPLE = """
  {
    "task_id": "20250218-1101-1908-6200-a5f7e25f798d",
    "state": "complete",
    "_tags": {
      "action_name": "curl-bleeding",
      "action_state": "complete",
      "api_key_id": "testing",
      "call_id": "20250218-1101-1908-8400-ba45a6b799e1",
      "request_id": "e407c5654b684bb4-TPX",
      "task_id": "20250218-1101-1908-6200-a5f7e25f798d"
    }
  }
"""


TASK_ITEM_EXAMPLE = """
{
  "task_id": "20250218-1113-2704-1800-6a4e7f2c2621",
  "state": "pending",
  "_tags": {
    "action_name": "curl-bleeding",
    "api_key_id": "testing",
    "request_id": "b459d6711ecf47bb-TPX",
    "task_id": "20250218-1113-2704-1800-6a4e7f2c2621"
  }
}
"""


from .base import BaseModelPrivateHandler
from .callback import Callback, CallbackHttp, CallbackSmtp
from .health import HealthResponse
from .task import TaskItem, TaskListItem, TaskState

__all__ = [
    "BaseModelPrivateHandler",
    "Callback",
    "CallbackHttp",
    "CallbackSmtp",
    "HealthResponse",
    "TaskListItem",
    "TaskItem",
    "TaskState",
]
