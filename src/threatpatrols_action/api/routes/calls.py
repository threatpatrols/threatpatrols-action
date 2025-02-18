import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from hlid import HLID

from ... import action_functions, action_models, config
from ...exceptions import ThreatPatrolsApiException, ThreatPatrolsException
from ...shared.lib.action_caller import foreground_action_caller
from ...shared.lib.state import get_state_handler
from ...shared.lib.strings import flatten_dict_as_string
from ...shared.validators.tags import validate_reserved_action_tags
from ..controllers import get_request_id_header, get_validated_api_key

ACTION_NAME = config.ACTION_NAME

router = APIRouter()
logger = logging.getLogger(config.LOGGER_NAME)
state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
)


@router.get(
    f"/{ACTION_NAME}/calls",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " direct action calls"],
    summary=f"Get a list of {ACTION_NAME!r} action call summary records.",
)
async def action_calls_get_list(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
) -> list[action_models.ActionListItem]:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    results = []
    for item in await state_handler.find_states(key="calls", extension="out"):
        results.append(item)

    return results


@router.get(
    f"/{ACTION_NAME}/calls/{{call_id}}",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " direct action calls"],
    summary=f"Get a full {ACTION_NAME!r} action call record by call_id.",
)
async def action_calls_get_item(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    call_id: str,
) -> action_models.ActionItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id

    try:
        call_data = await state_handler.load_state(key=state_key, extension="out")
    except ThreatPatrolsException as e:
        detail = "Unable to get Action call data"
        logger.error(detail, exc_info=e)
        raise ThreatPatrolsApiException(detail=detail, user_detail=detail + ", see logs for detail.", status_code=404)

    return action_models.ActionItem(**call_data).model_dump()  # NB: because _tags


@router.post(
    f"/{ACTION_NAME}/calls",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " direct action calls"],
    summary=f"Create a {ACTION_NAME!r} action call record and execute the action without going to background.",
)
async def action_calls_post(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    action_request: action_models.ActionRequest,
) -> action_models.ActionItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    # makes access to private attribute keys possible
    request_data = action_request.model_dump()

    # check for shenanigans
    validate_reserved_action_tags(tags=request_data.get("_tags"))

    call_id = str(HLID())

    request_data["_tags"]["action_name"] = ACTION_NAME
    request_data["_tags"]["api_key_id"] = api_key.get("id")
    request_data["_tags"]["request_id"] = request_id
    request_data["_tags"]["call_id"] = call_id
    request_data["_tags"]["action_state"] = "pending"
    request_data["_tags"] = dict(sorted(request_data["_tags"].items()))

    logger.info(flatten_dict_as_string(data=request_data["_tags"]))
    action_function = getattr(action_functions, ACTION_NAME)
    action_response = await foreground_action_caller(action_function, **request_data)

    if not action_response:
        return action_models.ActionItem(
            error_messages=["No result received from foreground_action_caller()"],
            _tags=request_data["_tags"],
        )

    # sanity check and log
    assert request_id == action_response._tags.get("request_id")
    logger.info(flatten_dict_as_string(data=action_response._tags))

    return action_response.model_dump()  # NB: required because private attribute keys
