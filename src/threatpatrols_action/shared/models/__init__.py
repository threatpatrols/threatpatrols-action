TASK_ITEM_SUMMARY_EXAMPLE = """
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

HEALTH_ITEM_EXAMPLE = """
{
  "cpu_usage_p": 0.149,
  "memory_used_p": 0.47,
  "machine": "x86_64",
  "memory_free": 7110524928,
  "memory_used": 22781775872,
  "nodename": "computer",
  "release": "6.8.0-52-generic",
  "sysname": "Linux",
  "vendor": "Ubuntu"
}
"""


from .base import BaseModelPrivateHandler
from .callback import (
    Callback,
    CallbackHttp,
    CallbackHttpMethod,
    CallbackS3Put,
    CallbackSend,
    CallbackSlack,
    CallbackSmtp,
    CallbackThreatpatrols,
)
from .health import HealthResponse
from .task import TaskItem, TaskItemSummary, TaskState

__all__ = [
    #
    "BaseModelPrivateHandler",
    #
    "Callback",
    "CallbackSend",
    #
    "CallbackHttp",
    "CallbackHttpMethod",
    "CallbackS3Put",
    "CallbackSlack",
    "CallbackSmtp",
    "CallbackThreatpatrols",
    #
    "HealthResponse",
    #
    "TaskItem",
    "TaskItemSummary",
    "TaskState",
]
