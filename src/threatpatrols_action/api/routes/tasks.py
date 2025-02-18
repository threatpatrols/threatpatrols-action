import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from hlid import HLID

from ... import action_functions, action_models, config
from ...exceptions import ThreatPatrolsApiException, ThreatPatrolsException
from ...shared.lib.action_caller import background_action_caller
from ...shared.lib.state import get_state_handler
from ...shared.lib.strings import flatten_dict_as_string
from ...shared.models import TaskItem, TaskListItem, TaskState
from ...shared.validators.tags import validate_reserved_action_tags
from ..controllers import get_request_id_header, get_validated_api_key

ACTION_NAME = config.ACTION_NAME

router = APIRouter()
logger = logging.getLogger(config.LOGGER_NAME)
state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__TASKS__TTL_SECONDS,
)


@router.get(
    f"/{ACTION_NAME}/tasks",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Get a list of {ACTION_NAME!r} background task summary records.",
)
async def action_tasks_get_list(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
) -> list[TaskListItem]:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    results = []
    for item in await state_handler.find_states(key="tasks"):
        results.append(TaskListItem(**item))

    return results


@router.get(
    f"/{ACTION_NAME}/tasks/{{task_id}}",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Get a full {ACTION_NAME} background task record by task_id.",
)
async def action_tasks_get_item(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    task_id: str,
) -> TaskItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id

    try:
        task_data = await state_handler.load_state(key=state_key)
    except ThreatPatrolsException as e:
        detail = "Unable to get Task data"
        logger.error(detail, exc_info=e)
        raise ThreatPatrolsApiException(detail=detail, user_detail=detail + ", see logs for detail.", status_code=404)

    return TaskItem(**task_data)


@router.post(
    f"/{ACTION_NAME}/tasks",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Create a {ACTION_NAME!r} background task record and enqueue the action to be executed.",
)
async def action_tasks_post(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    action_request: action_models.ActionRequest,
    background_tasks: BackgroundTasks,
) -> TaskItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    # makes access to private attribute keys possible
    request_data = action_request.model_dump()

    # check for shenanigans
    validate_reserved_action_tags(tags=request_data.get("_tags"))

    task_id = str(HLID())

    request_data["_tags"]["action_name"] = ACTION_NAME
    request_data["_tags"]["api_key_id"] = api_key.get("id")
    request_data["_tags"]["request_id"] = request_id
    request_data["_tags"]["task_id"] = task_id
    request_data["_tags"] = dict(sorted(request_data["_tags"].items()))

    logger.info(flatten_dict_as_string(data=request_data["_tags"]))
    task = TaskItem(task_id=task_id, state=TaskState.PENDING, _tags=request_data["_tags"])

    action_function = getattr(action_functions, ACTION_NAME)
    background_tasks.add_task(
        background_action_caller, action_function=action_function, task_id=task_id, **request_data
    )

    return task
