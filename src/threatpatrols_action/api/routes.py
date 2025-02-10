import logging
from typing import Annotated, Callable

import psutil
from fastapi import APIRouter, BackgroundTasks, Depends, Header
from fastapi.openapi.docs import get_swagger_ui_html

from .. import action_models, config, state_handlers
from ..exceptions import ThreatPatrolsApiException, ThreatPatrolsException
from ..shared.lib.hlid import HLID
from ..shared.lib.state import get_state_handler
from .action import background_action_caller, foreground_action_caller
from .controllers import check_reserved_action_tags, validate_bearer_token
from .models import HealthResponse, TaskResponse, TaskState

ACTION_NAME = config.ACTION_NAME
OPENAPI_FAVICON_URL = config.OPENAPI_FAVICON_URL

STATE_FILESYSTEM_ROOT_PATH = config.STATE_FILESYSTEM_ROOT_PATH


logger = logging.getLogger(config.LOGGER_NAME)


class ActionRoutes:

    router: APIRouter
    action_call: Callable

    def __init__(self, action: Callable):

        if not callable(action):
            raise ThreatPatrolsApiException(detail="ActionRoutes.action must be callable!")

        self.action_call = action  # callable action class

        state_handlers.StateHandler = get_state_handler(
            storage="filesystem", state_filesystem_root_path=STATE_FILESYSTEM_ROOT_PATH
        )

        self.router = APIRouter()

        if config.DEBUG:
            self.router.add_api_route(
                "/docs", self.swagger_ui_html, methods=["GET"], tags=["System"], include_in_schema=False
            )
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            tags=["System"],
            summary="Get basic system-health and system-status data.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}",
            self.action_foreground,
            methods=["POST"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title()],
            summary=f"Directly call the {ACTION_NAME} action without sending to background.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}/{{call_id}}",
            self.get_action_foreground_data,
            methods=["GET"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title()],
            summary=f"Get previous {ACTION_NAME} action call result data by call_id.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}/task",
            self.action_background_task,
            methods=["POST"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title()],
            summary=f"Enqueue a {ACTION_NAME} action as a background task.",
        )
        self.router.add_api_route(
            f"/{ACTION_NAME}/task/{{task_id}}",
            self.get_action_background_task_data,
            methods=["GET"],
            tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title()],
            summary=f"Get information on background task {ACTION_NAME} action.",
        )

    async def action_foreground(
        self,
        api_key: Annotated[validate_bearer_token, Depends()],
        action_request: action_models.ActionRequest,
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

    async def get_action_foreground_data(
        self,
        api_key: Annotated[validate_bearer_token, Depends()],
        call_id: str,
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> action_models.ActionResponse:

        state_key = "call/" + call_id.split("-")[0] + "/" + call_id

        try:
            call_data = await state_handlers.StateHandler.load_state(key=state_key, extension="out")
        except ThreatPatrolsException as e:
            detail = "Unable to get Action call data"
            logger.error(detail, exc_info=e)
            raise ThreatPatrolsApiException(
                detail=detail, user_detail=detail + ", see logs for detail.", status_code=404
            )

        return action_models.ActionResponse(**call_data)

    async def action_background_task(
        self,
        api_key: Annotated[validate_bearer_token, Depends()],
        action_request: action_models.ActionRequest,
        background_tasks: BackgroundTasks,
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

        state_key = "task/" + task_id.split("-")[0] + "/" + task_id
        await state_handlers.StateHandler.save_state(key=state_key, data=task_response)

        background_tasks.add_task(
            background_action_caller, self.action_call, task_id=task_id, **action_request.model_dump()
        )
        return task_response

    async def get_action_background_task_data(
        self,
        api_key: Annotated[validate_bearer_token, Depends()],
        task_id: str,
        request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
    ) -> TaskResponse:

        state_key = "task/" + task_id.split("-")[0] + "/" + task_id

        try:
            task_data = await state_handlers.StateHandler.load_state(key=state_key)
        except ThreatPatrolsException as e:
            detail = "Unable to get Task data"
            logger.error(detail, exc_info=e)
            raise ThreatPatrolsApiException(
                detail=detail, user_detail=detail + ", see logs for detail.", status_code=404
            )

        return TaskResponse(**task_data)

    async def health_check(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            memory_usage=psutil.virtual_memory().percent,
            cpu_usage=psutil.cpu_percent(),
        )

    async def swagger_ui_html(self):
        return get_swagger_ui_html(
            title=f"Action {ACTION_NAME.title()}",
            openapi_url="/openapi.json",
            swagger_favicon_url=OPENAPI_FAVICON_URL,
            swagger_ui_parameters={
                "defaultModelsExpandDepth": -1,  # prevent the model Schema table from rendering
                "displayOperationId": False,
                "displayRequestDuration": True,
                "tryItOutEnabled": True,
                "requestSnippets": True,
            },
        )
