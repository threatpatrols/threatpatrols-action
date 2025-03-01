import logging
from pathlib import Path

from ... import action_models, config
from ...shared.lib.s3put import s3put
from ..lib.casts import dict_to_flat_string
from ..lib.substitutions import string_substitutions
from ..models import CallbackS3Put, CallbackSend
from ..validators.hlids import validate_hlid
from . import state_handler

logger = logging.getLogger(config.LOGGER_NAME)


async def s3put_callback(action_name: str, call_id: str, callback_config: dict):
    try:
        await s3put_callback_wrapper(action_name, call_id, callback_config)
    except Exception as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        # NB: do not terminate


async def s3put_callback_wrapper(action_name: str, call_id: str, callback_config: dict):

    # confirm input and output state is available
    validate_hlid(call_id, location_hint="s3put_callback_wrapper")
    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    call_input = await state_handler.load_state(key=state_key, extension="in")

    callback = CallbackS3Put(action_name=action_name, call_id=call_id, **callback_config)
    substitutions = {**call_input.get("_tags", {}), **{"callback_name": callback.name}}
    request = {"url": string_substitutions(callback.url, substitutions=substitutions)}

    if callback.send == CallbackSend.SUMMARY:
        call_output = await state_handler.load_state(key=state_key, extension="out")
        call_summary = action_models.ActionItemSummary(**call_output).model_dump()
        await state_handler.save_state(key=state_key, data=call_summary, extension="summary")
        request["file"] = Path(state_handler.key_file(key=state_key, extension="summary"))
    elif callback.send == CallbackSend.OUTPUT:
        request["file"] = Path(state_handler.key_file(key=state_key, extension="out"))
    elif callback.send == CallbackSend.INPUT:
        request["file"] = Path(state_handler.key_file(key=state_key, extension="in"))

    response = s3put(**request)
    response_metadata = response.get("ResponseMetadata", {})
    response_status_code = response_metadata.get("HTTPStatusCode", 500)

    logger.debug("s3put response headers: " + dict_to_flat_string(response_metadata.get("HTTPHeaders")))

    log_message = (
        f"s3put callback: status_code={response_status_code} "
        f"action_name={callback.action_name} call_id={callback.call_id}"
    )

    if 299 >= response_status_code >= 200:
        logger.info(log_message)
        return

    logger.error(log_message)
