import logging

from hlid import HLID

from ... import action_functions, action_models, config
from ...exceptions import ThreatPatrolsException
from ...shared.lib.callers import foreground_action_caller
from ...shared.lib.casts import dict_to_flat_string
from ...shared.lib.state import get_state_handler
from ...shared.validators.hlids import validate_hlid

logger = logging.getLogger(config.LOGGER_NAME)
state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
)


async def tpas_call(action_name: str, action_args: dict, call_id: str = None) -> action_models.ActionItem:

    if not call_id:
        call_id = str(HLID())
    else:
        validate_hlid(call_id, location_hint="tpas_call")

    action_args["_tags"]["call_id"] = call_id
    action_args["_tags"] = dict(sorted(action_args["_tags"].items()))

    logger.info("Action start: " + dict_to_flat_string(data=action_args["_tags"]))
    action_function = getattr(action_functions, action_name)
    action_response = await foreground_action_caller(action_function, call_id=call_id, **action_args)

    if not action_response:
        raise ThreatPatrolsException(f"Empty result from action {action_name!r}.")

    # sanity check and log
    assert call_id == action_response._tags.get("call_id")
    logger.info("Action end: " + dict_to_flat_string(data=action_response._tags))

    # return all the things!
    return action_response.model_dump()


async def tpas_call_get(call_id: str) -> action_models.ActionItem:

    validate_hlid(call_id, location_hint="tpas_call_get")

    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    call_data = await state_handler.load_state(key=state_key, extension="out")

    return action_models.ActionItem(**call_data).model_dump()


async def tpas_call_list(
    filter_expired_ttl: bool = False, purge_expired_ttl: bool = False
) -> list[action_models.ActionItemSummary]:

    calls = []

    if filter_expired_ttl or purge_expired_ttl:
        for item in await state_handler.find_states(key="calls", extension="out", filter_expired_ttl=True):
            calls.append(action_models.ActionItemSummary(**item).model_dump())
        if purge_expired_ttl:
            logger.warning(f"Purging {len(calls)} expired_ttl calls from state storage.")
            for call in calls:
                call_id = call.get("_tags", {}).get("call_id")
                if not call_id:
                    continue
                state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
                await state_handler.remove_state(key=state_key, extension="in")
                await state_handler.remove_state(key=state_key, extension="out")
            calls = []
    else:
        for item in await state_handler.find_states(key="calls", extension="out", filter_expired_ttl=False):
            calls.append(action_models.ActionItemSummary(**item).model_dump())

    return calls
