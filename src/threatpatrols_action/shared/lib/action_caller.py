import logging
from inspect import signature
from typing import Callable
import platform

from hlid import HLID

from ... import action_models, config
from ...exceptions import ThreatPatrolsException
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskResponse, TaskState
from ...shared.validators.tags import validate_action_tags
from ..lib.background_task import background_task_observability

logger = logging.getLogger(config.LOGGER_NAME)


async def foreground_action_caller(action_function: Callable, *_, **kwargs):
    if _:
        raise ValueError("Unexpected positional argument in foreground_action_caller()")

    if not callable(action_function):
        raise ValueError("Action type not callable in foreground_action_caller()")

    hlid = HLID()
    call_id = str(hlid)

    if not kwargs:
        kwargs = {}
    if "_tags" not in kwargs.keys():
        kwargs["_tags"] = {}

    kwargs["_tags"]["action_name"] = config.ACTION_NAME
    kwargs["_tags"]["call_id"] = call_id
    kwargs["_tags"]["call_timestamp"] = str(hlid.datetime.replace(microsecond=0).isoformat())
    kwargs["_tags"]["platform_node"] = platform.node()
    kwargs["_tags"]["platform_machine"] = platform.machine()
    kwargs["_tags"]["state"] = "pending"
    validate_action_tags(tags=kwargs["_tags"])

    state_handler = get_state_handler(
        storage=config.STATE__TYPE,
        state_filesystem_root_path=config.STATE__PARAMS.get("root_path"),
        state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
    )

    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    await state_handler.save_state(key=state_key, data=kwargs, extension="in")

    if "_tags" in signature(action_function).parameters.keys():
        func_kwargs = {key: kwargs[key] for key in kwargs.keys() if (not key.startswith("_") or key == "_tags")}
    else:
        func_kwargs = {key: kwargs[key] for key in kwargs.keys() if not key.startswith("_")}

    try:
        result = action_function(**func_kwargs)
    except Exception as e:
        detail = f"Exception while calling Action for {call_id=}"
        logger.error(detail, exc_info=e)
        raise ThreatPatrolsException(detail)

    if not isinstance(result, action_models.ActionResponse):
        raise ThreatPatrolsException("Action response not a ActionResponse-type")

    result_tags = result.model_dump().get("_tags", {})  # funky approach required to get this private attribute
    result._tags = {**result_tags, **kwargs.get("_tags")}  # make sure the action is not able to overwrite tags
    result._tags["state"] = "complete"

    await state_handler.save_state(key=state_key, data=result, extension="out")
    return result


@background_task_observability
async def background_action_caller(action_function: Callable, *_, task_id: str, **kwargs) -> None:
    if _:
        raise ValueError("Unexpected positional argument in background_action_caller()")

    if not callable(action_function):
        raise ValueError("Action type not callable in background_action_caller()")

    tags = kwargs.get("_tags")
    validate_action_tags(tags=tags)

    state_handler = get_state_handler(
        storage=config.STATE__TYPE,
        state_ttl_seconds=config.STATE__TASKS__TTL_SECONDS,
        state_filesystem_root_path=config.STATE__PARAMS.get("root_path"),
    )

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    task_response = TaskResponse(task_id=task_id, state=TaskState.IN_PROGRESS, _tags=tags)
    await state_handler.save_state(key=state_key, data=task_response.model_dump())

    result = await foreground_action_caller(action_function, **kwargs)
    tags["call_id"] = result.tags.get("call_id")

    task_response = TaskResponse(task_id=task_id, state=TaskState.COMPLETE, _tags=tags)
    await state_handler.save_state(key=state_key, data=task_response.model_dump())
