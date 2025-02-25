import logging

from ... import config
from ..validators.hlids import validate_hlid
from . import state_handler

logger = logging.getLogger(config.LOGGER_NAME)


async def threatpatrols_callback(action_name: str, call_id: str, callback_config: dict):
    try:
        await threatpatrols_callback_wrapper(action_name, call_id, callback_config)
    except Exception as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        # NB: do not terminate


async def threatpatrols_callback_wrapper(action_name: str, call_id: str, callback_config: dict):

    # confirm input and output state is available
    validate_hlid(call_id, location_hint="threatpatrols_callback_wrapper")
    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id

    call_input = await state_handler.load_state(key=state_key, extension="in")
    call_output = await state_handler.load_state(key=state_key, extension="out")

    assert call_input is not None  # todo
    assert call_output is not None  # todo
