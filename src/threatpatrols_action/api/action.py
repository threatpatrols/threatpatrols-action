import datetime
import logging
from typing import Callable

from hlid import HLID

from .. import config, state_handlers
from ..exceptions import ThreatPatrolsException
from .lib.background_task import background_task_observability
from .models import TaskResponse, TaskState

USER_TAG_MAX_COUNT = config.USER_TAG_MAX_COUNT
USER_TAG_MAX_KEY_LENGTH = config.USER_TAG_MAX_KEY_LENGTH
USER_TAG_MAX_VALUE_LENGTH = config.USER_TAG_MAX_VALUE_LENGTH

logger = logging.getLogger(config.LOGGER_NAME)


async def foreground_action_caller(action: Callable, *_, **kwargs):
    if _:
        raise ValueError("Unexpected positional argument in foreground_action_caller()")

    if not callable(action):
        raise ValueError("Action type not callable in foreground_action_caller()")

    if not kwargs:
        kwargs = {}
    if "tags" not in kwargs.keys():
        kwargs["tags"] = {}

    call_id = str(HLID())

    kwargs["tags"]["call_id"] = call_id
    kwargs["tags"]["call_timestamp"] = str(
        datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0).isoformat()
    )
    validate_action_tags(tags=kwargs["tags"])

    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    await state_handlers.StateHandler.save_state(key=state_key, data=kwargs, extension="in")

    try:
        result = action(**kwargs)
    except Exception as e:
        detail = f"Exception while calling Action for {call_id=}"
        logger.error(detail, exc_info=e)
        raise ThreatPatrolsException(detail)

    await state_handlers.StateHandler.save_state(key=state_key, data=result, extension="out")
    return result


@background_task_observability
async def background_action_caller(action: Callable, *_, task_id: str, **kwargs) -> None:
    if _:
        raise ValueError("Unexpected positional argument in background_action_caller()")

    if not callable(action):
        raise ValueError("Action type not callable in background_action_caller()")

    tags = kwargs.get("tags")

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    task_response = TaskResponse(task_id=task_id, state=TaskState.IN_PROGRESS, tags=tags)
    await state_handlers.StateHandler.save_state(key=state_key, data=task_response.model_dump())

    result = await foreground_action_caller(action, **kwargs)
    tags["call_id"] = result.tags.get("call_id")

    task_response = TaskResponse(task_id=task_id, state=TaskState.COMPLETE, tags=tags)
    await state_handlers.StateHandler.save_state(key=state_key, data=task_response.model_dump())


def validate_action_tags(tags):
    if len(tags) > USER_TAG_MAX_COUNT:
        raise ValueError(f"User supplied tags exceeds {USER_TAG_MAX_COUNT} limit per action request")

    if any(len(str(v)) > USER_TAG_MAX_VALUE_LENGTH for v in tags.values()):
        raise ValueError(f"User supplied tag-value exceeds {USER_TAG_MAX_VALUE_LENGTH} length in action request")

    if any(len(str(k)) > USER_TAG_MAX_KEY_LENGTH for k in tags.keys()):
        raise ValueError(f"User supplied tag-key exceeds {USER_TAG_MAX_KEY_LENGTH} length in action request")
