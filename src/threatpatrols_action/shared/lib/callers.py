import logging
import platform
from functools import wraps
from inspect import signature
from typing import Any, Callable

from hlid import HLID

from ... import action_models, config
from ...exceptions import ThreatPatrolsException
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskItem, TaskState
from ...shared.validators.hlids import validate_hlid
from ...shared.validators.tags import validate_action_tags
from ..callbacks import callback_function_map

logger = logging.getLogger(config.LOGGER_NAME)


async def handle_callbacks(callbacks: list[str], action_name: str, call_id: str):

    if not isinstance(callbacks, list):
        raise ThreatPatrolsException("Callbacks must be supplied as list of callback names.")

    for callback in callbacks:
        if "." not in str(callback):
            raise ThreatPatrolsException("Callbacks must be supplied in format 'callback-name.callback-config-key'.")
        callback_name, callback_key_name = str(callback).split(".", maxsplit=1)

        try:
            await callback_caller(callback_name, callback_key_name, action_name, call_id)
        except Exception as e:
            # NB: do not allow a broken callback to terminate the rest of the callback list
            logger.error(str(e))
            logger.debug("stack-trace", exc_info=e)


async def callback_caller(callback_name: str, callback_key_name: str, action_name: str, call_id: str):

    # validate the call_id
    validate_hlid(call_id, location_hint="callback_caller")

    # check the callback is configured for use
    callback_config = config.get("callbacks", {}).get(callback_name, {}).get(callback_key_name)
    if not callback_config:
        raise ThreatPatrolsException(f"Callback {callback_name}.{callback_key_name} not defined in config.")

    if callback_name not in callback_function_map.keys():
        raise ThreatPatrolsException(f"Callback {callback_name} not known here.")

    logger.info(f"Invoking callback: {callback_name}.{callback_key_name} for {action_name=} {call_id=}")
    await callback_function_map[callback_name](action_name, call_id, callback_config)


async def foreground_action_caller(
    action_function: Callable, *_, call_id: str = None, **kwargs
) -> action_models.ActionItem:
    if _:
        raise ValueError("Unexpected positional argument in foreground_action_caller()")

    if not callable(action_function):
        raise ValueError("Action type not callable in foreground_action_caller()")

    logger.debug(f"foreground_action_caller(): {call_id=} {kwargs=}")

    validate_action_tags(tags=kwargs.get("_tags"))

    if not call_id:
        call_id = str(HLID())
    else:
        validate_hlid(call_id, location_hint="foreground_action_caller")

    kwargs["_tags"]["action_name"] = config.ACTION_NAME
    kwargs["_tags"]["action_title"] = config.ACTION_NAME.replace("-", " ").replace("_", " ").title()
    kwargs["_tags"]["action_state"] = TaskState.PENDING
    kwargs["_tags"]["call_id"] = call_id
    kwargs["_tags"]["call_id_prefix"] = call_id.split("-")[0]
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

    # provide observability of the call tags within the action function if it has a _tags parameter
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

    # handle tags
    try:
        _ = result._tags
    except AttributeError:
        raise ThreatPatrolsException(
            "Action result does not contain '_tags' attribute, check it inherits from BaseModelPrivateHandler"
        )
    result._tags = {**result._tags, **kwargs.get("_tags")}  # make sure action results cannot overwrite request tags

    # insert _callbacks information into results data
    result._callbacks = kwargs["_callbacks"]

    # handle callbacks
    result._tags["action_state"] = TaskState.CALLBACKS_IN_PROGRESS
    await state_handler.save_state(key=state_key, data=result.model_dump(), extension="out")
    await handle_callbacks(callbacks=kwargs["_callbacks"], action_name=kwargs["_tags"]["action_name"], call_id=call_id)

    result._tags["action_state"] = TaskState.COMPLETE
    await state_handler.save_state(key=state_key, data=result.model_dump(), extension="out")
    return result


def background_task_observability(func: Callable) -> Callable:
    """
    Function decorator that provides observability for background tasks via logged-tasks and
    logged-exceptions
    Credit: https://johachi.hashnode.dev/important-gotchas-with-backgroundtasks-in-fastapi
    """
    task_name = func.__name__

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:

        #
        # NB: failures inside this function are >>SILENT<<  If something related to background tasks is not
        # working, then consider this function carefully.  Don't be in a rush to change the code in this function!
        #

        if not kwargs.get("_tags") or not kwargs.get("_tags", {}).get("task_id"):
            logger.error("Background tasks MUST provide '_tags.task_id' value in kwargs.")
            return

        task_id = kwargs.get("_tags", {}).get("task_id", "anonymous")
        logger.info(f"background_task [{task_id}] {task_name}() started.")

        try:
            await func(*args, **kwargs)
            logger.info(f"background_task [{task_id}] {task_name}() finished successfully")
        except Exception as e:
            log_message = f"background_task [{task_id}] {task_name}() failed permanently with error: {e.__repr__()!r}"
            if logger.level <= 10:  # 10 == logging.DEBUG
                logger.error(msg=log_message, exc_info=True)
            else:
                logger.error(msg=log_message)

    return wrapper


@background_task_observability
async def background_action_caller(action_function: Callable, *_, task_id: str = None, **kwargs) -> None:
    if _:
        raise ValueError("Unexpected positional argument in background_action_caller()")

    if not callable(action_function):
        raise ValueError("Action type not callable in background_action_caller()")

    if "_tags" not in kwargs.keys():
        raise ThreatPatrolsException("Background action caller supplied without _tags kwarg.")

    if "_callbacks" not in kwargs.keys():
        raise ThreatPatrolsException("Background action caller supplied without _callbacks kwarg.")

    logger.debug(f"background_action_caller(): {task_id=} {kwargs=}")

    validate_action_tags(tags=kwargs["_tags"])

    validate_hlid(task_id, location_hint="background_action_caller")
    assert task_id == kwargs.get("_tags", {}).get("task_id")
    kwargs["_tags"]["task_id_prefix"] = task_id.split("-")[0]

    state_handler = get_state_handler(
        method=config.STATE__METHOD,
        method_params=config.STATE__PARAMS,
        state_ttl_seconds=config.STATE__TASKS__TTL_SECONDS,
    )

    call_id = str(HLID())

    kwargs["_tags"]["call_id"] = call_id
    kwargs["_tags"]["call_id_prefix"] = call_id.split("-")[0]

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    task_item = TaskItem(task_id=task_id, state=TaskState.ACTION_IN_PROGRESS, _tags=kwargs["_tags"])
    await state_handler.save_state(key=state_key, data=task_item.model_dump())

    result = await foreground_action_caller(action_function, call_id=call_id, **kwargs)
    tags = dict(sorted({**kwargs["_tags"], **result._tags}.items()))
    task_item = TaskItem(task_id=task_id, state=TaskState.COMPLETE, _tags=tags, _callbacks=kwargs["_callbacks"])

    await state_handler.save_state(key=state_key, data=task_item.model_dump())
