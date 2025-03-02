import json
import logging

from slack_sdk import WebClient

from ... import action_models, config
from ..lib.substitutions import string_substitutions
from ..models import CallbackSend, CallbackSlack
from ..validators.hlids import validate_hlid
from . import get_callback_send_data

logger = logging.getLogger(config.LOGGER_NAME)


async def slack_callback(action_name: str, call_id: str, callback_config: dict):
    try:
        await slack_callback_wrapper(action_name, call_id, callback_config)
    except Exception as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        # NB: do not terminate


async def slack_callback_wrapper(action_name: str, call_id: str, callback_config: dict):

    # confirm input and output state is available
    validate_hlid(call_id, location_hint="slack_callback_wrapper")
    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    callback = CallbackSlack(action_name=action_name, call_id=call_id, **callback_config)
    summary_data = await get_callback_send_data(
        send=CallbackSend.SUMMARY, state_key=state_key, summary_model=action_models.ActionItemSummary
    )

    client = WebClient(token=string_substitutions(callback.token))
    if callback.send:
        send_data = await get_callback_send_data(
            send=callback.send,
            state_key=state_key,
            summary_model=action_models.ActionItemSummary,
        )
        response = client.files_upload_v2(
            content=json.dumps(send_data, indent="  ").encode(),
            filename=f"{callback.send.value}.json",
            channel=string_substitutions(callback.channel, substitutions=summary_data),
            initial_comment=string_substitutions(callback.message, substitutions=summary_data),
        )
    else:
        response = client.chat_postMessage(
            channel=string_substitutions(callback.channel, substitutions=summary_data),
            text=string_substitutions(callback.message, substitutions=summary_data),
        )

    log_message = (
        f"slack callback: status_code={response.status_code} "
        f"action_name={callback.action_name} call_id={callback.call_id}"
    )

    if 299 >= response.status_code >= 200:
        logger.info(log_message)
        return

    logger.error(log_message)
