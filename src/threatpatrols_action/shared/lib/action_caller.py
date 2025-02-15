import datetime
import logging
from typing import Callable

from hlid import HLID

from ... import config
from ...exceptions import ThreatPatrolsException
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskResponse, TaskState
from ...shared.validators.tags import validate_action_tags
from ..lib.background_task import background_task_observability

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

    state_handler = get_state_handler(
        storage=config.STATE__TYPE,
        state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
        state_filesystem_root_path=config.STATE__PARAMS.get("root_path"),
    )

    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    await state_handler.save_state(key=state_key, data=kwargs, extension="in")

    try:
        result = action(**kwargs)
    except Exception as e:
        detail = f"Exception while calling Action for {call_id=}"
        logger.error(detail, exc_info=e)
        raise ThreatPatrolsException(detail)

    await state_handler.save_state(key=state_key, data=result, extension="out")
    return result


@background_task_observability
async def background_action_caller(action: Callable, *_, task_id: str, **kwargs) -> None:
    if _:
        raise ValueError("Unexpected positional argument in background_action_caller()")

    if not callable(action):
        raise ValueError("Action type not callable in background_action_caller()")

    tags = kwargs.get("tags")
    validate_action_tags(tags=tags)

    state_handler = get_state_handler(
        storage=config.STATE__TYPE,
        state_ttl_seconds=config.STATE__TASKS__TTL_SECONDS,
        state_filesystem_root_path=config.STATE__PARAMS.get("root_path"),
    )

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    task_response = TaskResponse(task_id=task_id, state=TaskState.IN_PROGRESS, tags=tags)
    await state_handler.save_state(key=state_key, data=task_response.model_dump())

    result = await foreground_action_caller(action, **kwargs)
    tags["call_id"] = result.tags.get("call_id")

    task_response = TaskResponse(task_id=task_id, state=TaskState.COMPLETE, tags=tags)
    await state_handler.save_state(key=state_key, data=task_response.model_dump())
