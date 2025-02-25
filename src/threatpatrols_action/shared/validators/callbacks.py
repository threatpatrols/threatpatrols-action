import logging
from typing import Optional

from ... import config
from ...exceptions import ThreatPatrolsException
from ..callbacks import callback_function_map, callback_model_map

logger = logging.getLogger(config.LOGGER_NAME)


def callbacks_validator(callbacks: Optional[dict] = None):

    if not callbacks:
        return

    for callback_name, callback_definitions in callbacks.items():
        for callback_key_name, callback_definition in callback_definitions.items():
            logger.debug(f"Validating callback {callback_name}.{callback_key_name}")
            validate_callback(callback_name, callback_definition)


def validate_callback(callback_name, callback_definition):

    if callback_name not in callback_function_map.keys():
        raise ThreatPatrolsException(f"Callback {callback_name} not a known callback_function here.")

    if callback_name not in callback_model_map.keys():
        raise ThreatPatrolsException(f"Callback {callback_name} not a known callback_model here.")

    faux_action_name = f"validate_{callback_name}"
    faux_call_id = "20000101-0000-0000-0000-000000000000"
    callback_model_map[callback_name](action_name=faux_action_name, call_id=faux_call_id, **callback_definition)
