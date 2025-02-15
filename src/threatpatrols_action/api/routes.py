import logging
from typing import Annotated, Callable

import psutil
from fastapi import APIRouter, BackgroundTasks, Depends, Header
from hlid import HLID

from .. import action_models, config, state_handlers
from ..exceptions import ThreatPatrolsApiException, ThreatPatrolsException
from ..shared.lib.action_caller import background_action_caller, foreground_action_caller
from ..shared.lib.state import get_state_handler
from ..shared.models import HealthResponse, TaskListItemResponse, TaskResponse, TaskState
from .controllers import check_reserved_action_tags, validate_bearer_token
from .lib.swagger import get_swagger_docs_response

ACTION_NAME = config.ACTION_NAME

STATE__TYPE = config.STATE__TYPE
STATE__PARAMS___ROOT_PATH = config.STATE__PARAMS.get("root_path")


logger = logging.getLogger(config.LOGGER_NAME)


class ActionRoutes:

    router: APIRouter
    action_call: Callable

    def __init__(self, action: Callable):

        if not callable(action):
            raise ThreatPatrolsApiException(detail="ActionRoutes.action must be callable!")

        self.action_call = action  # callable action class

        state_handlers.StateHandler = get_state_handler(
            storage=STATE__TYPE,
            state_filesystem_root_path=STATE__PARAMS___ROOT_PATH,
        )

        self.router = APIRouter()

        if config.DEBUG:
            self.router.add_api_route(
                "/docs", get_swagger_docs_response, methods=["GET"], tags=["System"], include_in_schema=False
            )
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            tags=["System"],
            summary="Get basic system-health and system-status data.",
        )

        # Call
        self.router.add_api_route(
            f"/{ACTION_NAME}/calls",
            self.action_calls_get_list,
            methods=["GET"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Direct"],
            summary=f"Get a list of {ACTION_NAME!r} action call summary records.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}/calls/{{call_id}}",
            self.action_calls_get_item,
            methods=["GET"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Direct"],
            summary=f"Get a full {ACTION_NAME!r} action call record by call_id.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}/calls",
            self.action_calls_post,
            methods=["POST"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Direct"],
            summary=f"Create a {ACTION_NAME!r} action call record and execute the action without going to background.",
        )

        # Task
        self.router.add_api_route(
            f"/{ACTION_NAME}/tasks",
            self.action_tasks_get_list,
            methods=["GET"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Background"],
            summary=f"Get a list of {ACTION_NAME!r} background task summary records.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}/tasks/{{task_id}}",
            self.action_tasks_get_item,
            methods=["GET"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Background"],
            summary=f"Get a full {ACTION_NAME} background task record by task_id.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}/tasks",
            self.action_tasks_post,
            methods=["POST"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Background"],
            summary=f"Create a {ACTION_NAME!r} background task record and enqueue the action to be executed.",
        )

    async def action_calls_get_list(
        self,
        api_key: Annotated[validate_bearer_token, Depends()],
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> list[action_models.ActionListItemResponse]:

        results = []
        for item in await state_handlers.StateHandler.find_states(key="calls", extension="out"):
            results.append(action_models.ActionListItemResponse(**item))

        return results

    async def action_calls_get_item(
        self,
        call_id: str,
        api_key: Annotated[validate_bearer_token, Depends()],
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> action_models.ActionResponse:

        state_key = "calls/" + call_id.split("-")[0] + "/" + call_id

        try:
            call_data = await state_handlers.StateHandler.load_state(key=state_key, extension="out")
        except ThreatPatrolsException as e:
            detail = "Unable to get Action call data"
            logger.error(detail, exc_info=e)
            raise ThreatPatrolsApiException(
                detail=detail, user_detail=detail + ", see logs for detail.", status_code=404
            )

        return action_models.ActionResponse(**call_data)

    async def action_calls_post(
        self,
        action_request: action_models.ActionRequest,
        api_key: Annotated[validate_bearer_token, Depends()],
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> action_models.ActionResponse:

        # check for shenanigans
        check_reserved_action_tags(tags=action_request.tags)

        api_key_id = api_key.get("id")
        action_request.tags["action_name"] = action_name = config.ACTION_NAME
        action_request.tags["api_key_id"] = api_key_id
        action_request.tags["request_id"] = request_id

        logger.info(f"status=called action_name={action_name} api_key_id={api_key_id}")
        action_response = await foreground_action_caller(self.action_call, **action_request.model_dump())

        if not action_response:
            return action_models.ActionResponse(
                tags=action_request.tags,
                error_messages=["No result received from foreground_action_call()"],
            )

        call_id = action_response.tags.get("call_id")
        logger.info(f"status=complete action_name={action_name} api_key_id={api_key_id}, call_id={call_id}")

        return action_response

    async def action_tasks_get_list(
        self,
        api_key: Annotated[validate_bearer_token, Depends()],
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> list[TaskListItemResponse]:

        # poke key_file to get the tasks base path
        # task_base_path = state_handlers.StateHandler.key_file(key="task/poke").parent
        # print(task_base_path)

        # TODO: get a list of the action items and return

        return []

    async def action_tasks_post(
        self,
        action_request: action_models.ActionRequest,
        background_tasks: BackgroundTasks,
        api_key: Annotated[validate_bearer_token, Depends()],
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> TaskResponse:

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
        await state_handlers.StateHandler.save_state(key=state_key, data=task_response)

        background_tasks.add_task(
            background_action_caller, self.action_call, task_id=task_id, **action_request.model_dump()
        )
        return task_response

    async def action_tasks_get_item(
        self,
        task_id: str,
        api_key: Annotated[validate_bearer_token, Depends()],
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> TaskResponse:

        state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id

        try:
            task_data = await state_handlers.StateHandler.load_state(key=state_key)
        except ThreatPatrolsException as e:
            detail = "Unable to get Task data"
            logger.error(detail, exc_info=e)
            raise ThreatPatrolsApiException(
                detail=detail, user_detail=detail + ", see logs for detail.", status_code=404
            )

        return TaskResponse(**task_data)

    async def health_check(self, background_tasks: BackgroundTasks) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            memory_usage=psutil.virtual_memory().percent,
            cpu_usage=psutil.cpu_percent(),
            background_tasks=len(background_tasks.tasks),
        )
