import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ... import action_models, config
from ...shared.controllers.calls import tpas_call, tpas_call_get, tpas_call_list
from ...shared.lib.state import get_state_handler
from ...shared.validators.tags import validate_reserved_action_tags
from ..lib.headers import get_request_id_header, get_validated_api_key

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
    summary=f"Get a list of the {ACTION_NAME!r} action call summaries.",
)
async def action_calls_get_list(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
) -> list[action_models.ActionListItem]:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    return await tpas_call_list()


@router.get(
    f"/{ACTION_NAME}/calls/{{call_id}}",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " direct action calls"],
    summary=f"Get a single {ACTION_NAME!r} action-call record by call_id.",
)
async def action_calls_get_item(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    call_id: str,
) -> action_models.ActionItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    return await tpas_call_get(call_id)


@router.post(
    f"/{ACTION_NAME}/calls",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " direct action calls"],
    summary=f"Create a {ACTION_NAME!r} action-call record and execute the action without going to background.",
)
async def action_calls_post(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    action_request: action_models.ActionRequest,
) -> action_models.ActionItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    action_args = action_request.model_dump()

    # check for tag shenanigans
    validate_reserved_action_tags(tags=action_args.get("_tags"))

    # add some request specific tags
    action_args["_tags"]["request_id"] = request_id
    action_args["_tags"]["api_key_id"] = api_key.get("id")

    return await tpas_call(action_name=ACTION_NAME, action_args=action_args)
