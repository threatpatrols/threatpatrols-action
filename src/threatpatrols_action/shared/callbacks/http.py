import logging

from ... import action_models, config
from ..lib.http_client import HttpClient
from ..lib.string import string_substitutions
from ..models import CallbackHttp, CallbackHttpMethod, CallbackSend
from ..validators.hlids import validate_hlid
from . import state_handler

logger = logging.getLogger(config.LOGGER_NAME)


async def http_callback(action_name: str, call_id: str, callback_config: dict):
    try:
        await http_callback_wrapper(action_name, call_id, callback_config)
    except Exception as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        # NB: do not terminate


async def http_callback_wrapper(action_name: str, call_id: str, callback_config: dict):

    # confirm input and output state is available
    validate_hlid(call_id, location_hint="http_callback_wrapper")
    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id

    call_input = await state_handler.load_state(key=state_key, extension="in")
    call_output = await state_handler.load_state(key=state_key, extension="out")

    callback = CallbackHttp(action_name=action_name, call_id=call_id, **callback_config)
    substitutions = {**call_input.get("_tags", {}), **{"callback_name": callback.name}}

    request = {
        "method": callback.method.value,
        "url": string_substitutions(callback.url, substitutions=substitutions),
        "headers": callback.headers,
    }

    if not callback.method != CallbackHttpMethod.GET:
        if callback.send == CallbackSend.SUMMARY:
            request["data"] = action_models.ActionItemSummary(**call_output).model_dump()
        elif callback.send == CallbackSend.OUTPUT:
            request["data"] = action_models.ActionItem(**call_output).model_dump()
        elif callback.send == CallbackSend.INPUT:
            request["data"] = action_models.ActionItem(**call_input).model_dump()

    http_client = HttpClient(proxy=callback.proxy, verify=callback.verify)
    response = await http_client.request(**request)

    log_message = (
        f"HTTP callback: status_code={response.status_code} "
        f"action_name={callback.action_name} call_id={callback.call_id}"
    )

    if 299 >= response.status_code >= 200:
        logger.info(log_message)
        return

    logger.error(log_message)
