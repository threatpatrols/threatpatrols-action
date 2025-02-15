import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from hlid import HLID

from ... import action_functions, action_models, config
from ...exceptions import ThreatPatrolsApiException, ThreatPatrolsException
from ...shared.lib.action_caller import background_action_caller
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskListItemResponse, TaskResponse, TaskState
from ..controllers import check_reserved_action_tags, validate_bearer_token

ACTION_NAME = config.ACTION_NAME

router = APIRouter()
logger = logging.getLogger(config.LOGGER_NAME)
state_handler = get_state_handler(
    storage=config.STATE__TYPE,
    state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
    state_filesystem_root_path=config.STATE__PARAMS.get("root_path"),
)


@router.get(
    f"/{ACTION_NAME}/tasks",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Get a list of {ACTION_NAME!r} background task summary records.",
)
async def action_tasks_get_list(
    api_key: Annotated[validate_bearer_token, Depends()],
    request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
) -> list[TaskListItemResponse]:
    assert api_key is not None
    assert request_id is not None

    # TODO: get a list of the action items and return
    return []


@router.get(
    f"/{ACTION_NAME}/tasks/{{task_id}}",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Get a full {ACTION_NAME} background task record by task_id.",
)
async def action_tasks_get_item(
    task_id: str,
    api_key: Annotated[validate_bearer_token, Depends()],
    request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
) -> TaskResponse:
    assert api_key is not None
    assert request_id is not None

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id

    try:
        task_data = await state_handler.load_state(key=state_key)
    except ThreatPatrolsException as e:
        detail = "Unable to get Task data"
        logger.error(detail, exc_info=e)
        raise ThreatPatrolsApiException(detail=detail, user_detail=detail + ", see logs for detail.", status_code=404)

    return TaskResponse(**task_data)


@router.post(
    f"/{ACTION_NAME}/tasks",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Create a {ACTION_NAME!r} background task record and enqueue the action to be executed.",
)
async def action_tasks_post(
    action_request: action_models.ActionRequest,
    background_tasks: BackgroundTasks,
    api_key: Annotated[validate_bearer_token, Depends()],
    request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
) -> TaskResponse:
    assert api_key is not None
    assert request_id is not None

    # check for shenanigans
    check_reserved_action_tags(tags=action_request.tags)

    api_key_id = api_key.get("id")
    action_request.tags["action_name"] = action_name = config.ACTION_NAME
    action_request.tags["api_key_id"] = api_key_id
    action_request.tags["request_id"] = request_id
    action_request.tags["task_id"] = task_id = str(HLID())

    logger.info(f"action_name={action_name} api_key_id={api_key_id} task_id={task_id}")
    task_response = TaskResponse(task_id=task_id, state=TaskState.PENDING, tags=action_request.tags)

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    await state_handler.save_state(key=state_key, data=task_response)

    action_function = getattr(action_functions, config.ACTION_NAME)
    background_tasks.add_task(background_action_caller, action_function, task_id=task_id, **action_request.model_dump())
    return task_response
