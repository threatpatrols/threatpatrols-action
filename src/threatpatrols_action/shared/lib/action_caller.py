import logging
import platform
from inspect import signature
from typing import Callable

from hlid import HLID

from ... import action_models, config
from ...exceptions import ThreatPatrolsException
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskItem, TaskState
from ...shared.validators.tags import validate_action_tags
from ..lib.background_task import background_task_observability

logger = logging.getLogger(config.LOGGER_NAME)


async def foreground_action_caller(
    action_function: Callable, *_, call_id: str = None, **kwargs
) -> action_models.ActionItem:
    if _:
        raise ValueError("Unexpected positional argument in foreground_action_caller()")

    if not callable(action_function):
        raise ValueError("Action type not callable in foreground_action_caller()")

    validate_action_tags(tags=kwargs.get("_tags"))

    if call_id:
        try:
            assert HLID(call_id).age > 0
        except Exception:
            raise ValueError("Invalid call_id supplied in foreground_action_caller()")
    else:
        call_id = str(HLID())
        logger.info(f"Background action call_id created {call_id=}")

    kwargs["_tags"]["action_name"] = config.ACTION_NAME
    kwargs["_tags"]["action_state"] = "pending"
    kwargs["_tags"]["call_id"] = call_id
    kwargs["_tags"]["call_timestamp"] = str(HLID(call_id).datetime.replace(microsecond=0).isoformat())
    kwargs["_tags"]["platform_node"] = platform.node()
    kwargs["_tags"]["platform_machine"] = platform.machine()
    validate_action_tags(tags=kwargs["_tags"])

    state_handler = get_state_handler(
        method=config.STATE__METHOD,
        method_params=config.STATE__PARAMS,
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

    if not isinstance(result, action_models.ActionItem):
        raise ThreatPatrolsException("Action response not a ActionItem-type")

    result._tags = {**result._tags, **kwargs.get("_tags")}  # make sure the results are not able to overwrite request
    result._tags["action_state"] = "complete"

    await state_handler.save_state(key=state_key, data=result, extension="out")
    return result


@background_task_observability
async def background_action_caller(action_function: Callable, *_, task_id: str = None, **kwargs) -> None:
    if _:
        raise ValueError("Unexpected positional argument in background_action_caller()")

    if not callable(action_function):
        raise ValueError("Action type not callable in background_action_caller()")

    validate_action_tags(tags=kwargs["_tags"])

    if task_id:
        try:
            assert HLID(task_id).age > 0
        except Exception:
            raise ValueError("Invalid task_id supplied")
    else:
        task_id = str(HLID())
        logger.info(f"Background action task_id created {task_id=}")

    state_handler = get_state_handler(
        method=config.STATE__METHOD,
        method_params=config.STATE__PARAMS,
        state_ttl_seconds=config.STATE__TASKS__TTL_SECONDS,
    )

    call_id = str(HLID())
    kwargs["_tags"]["call_id"] = call_id

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    task_item = TaskItem(task_id=task_id, state=TaskState.IN_PROGRESS, _tags=kwargs["_tags"])
    await state_handler.save_state(key=state_key, data=task_item.model_dump())

    result = await foreground_action_caller(action_function, call_id=call_id, **kwargs)
    tags = dict(sorted({**kwargs["_tags"], **result._tags}.items()))
    task_item = TaskItem(task_id=task_id, state=TaskState.COMPLETE, _tags=tags)

    await state_handler.save_state(key=state_key, data=task_item.model_dump())
