import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from ... import action_functions, action_models, config
from ...exceptions import ThreatPatrolsApiException, ThreatPatrolsException
from ...shared.lib.action_caller import foreground_action_caller
from ...shared.lib.state import get_state_handler
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
    f"/{ACTION_NAME}/calls",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Direct"],
    summary=f"Get a list of {ACTION_NAME!r} action call summary records.",
)
async def action_calls_get_list(
    api_key: Annotated[validate_bearer_token, Depends()],
    request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
) -> list[action_models.ActionListItemResponse]:
    assert api_key is not None
    assert request_id is not None

    results = []
    for item in await state_handler.find_states(key="calls", extension="out"):
        results.append(action_models.ActionListItemResponse(**item))

    return results


@router.get(
    f"/{ACTION_NAME}/calls/{{call_id}}",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Direct"],
    summary=f"Get a full {ACTION_NAME!r} action call record by call_id.",
)
async def action_calls_get_item(
    call_id: str,
    api_key: Annotated[validate_bearer_token, Depends()],
    request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
) -> action_models.ActionResponse:
    assert api_key is not None
    assert request_id is not None

    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id

    try:
        call_data = await state_handler.load_state(key=state_key, extension="out")
    except ThreatPatrolsException as e:
        detail = "Unable to get Action call data"
        logger.error(detail, exc_info=e)
        raise ThreatPatrolsApiException(detail=detail, user_detail=detail + ", see logs for detail.", status_code=404)

    return action_models.ActionResponse(**call_data)


@router.post(
    f"/{ACTION_NAME}/calls",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " Direct"],
    summary=f"Create a {ACTION_NAME!r} action call record and execute the action without going to background.",
)
async def action_calls_post(
    action_request: action_models.ActionRequest,
    api_key: Annotated[validate_bearer_token, Depends()],
    request_id: str = Header(None, include_in_schema=False),  # NB: request_id from "Request-Id" header
) -> action_models.ActionResponse:
    assert api_key is not None
    assert request_id is not None

    # check for shenanigans
    check_reserved_action_tags(tags=action_request.tags)

    api_key_id = api_key.get("id")
    action_request.tags["action_name"] = config.ACTION_NAME
    action_request.tags["api_key_id"] = api_key_id
    action_request.tags["request_id"] = request_id

    logger.info(f"status=called action_name={config.ACTION_NAME} api_key_id={api_key_id}")
    action_function = getattr(action_functions, config.ACTION_NAME)
    action_response = await foreground_action_caller(action_function, **action_request.model_dump())

    if not action_response:
        return action_models.ActionResponse(
            tags=action_request.tags,
            error_messages=["No result received from foreground_action_call()"],
        )

    call_id = action_response.tags.get("call_id")
    logger.info(f"status=complete action_name={config.ACTION_NAME} api_key_id={api_key_id}, call_id={call_id}")

    return action_response
