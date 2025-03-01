import logging
import os
from typing import Optional

from ... import config

logger = logging.getLogger(config.LOGGER_NAME)


def string_substitutions(value: str, substitutions: Optional[dict] = None, env_substitutions: bool = True):

    replacements = {}

    # env_substitutions; must occur before supplied substitutions
    # ===
    if env_substitutions:
        for env_key, env_value in os.environ.items():
            token = "${" + env_key + "}"
            if token in value:
                replacements[env_key] = env_value
                value = value.replace(token, token.lstrip("$"))

    # supplied substitutions
    # ===
    if isinstance(substitutions, dict):
        if "task_id" in substitutions.keys():
            substitutions["task_id_prefix"] = substitutions.get("task_id").split("-")[0]
        if "call_id" in substitutions.keys():
            substitutions["call_id_prefix"] = substitutions.get("call_id").split("-")[0]
        for tag_key, tag_value in substitutions.items():
            token = "{" + tag_key + "}"
            if token in value:
                replacements[tag_key] = tag_value

    try:
        return value.format(**replacements)
    except KeyError as e:
        logger.warning(f"Unknown replacement token {str(e)} encountered, token will not be replaced.")
        return value


def dict_value_substitutions(data: dict, substitutions: Optional[dict] = None, env_substitutions: bool = True):

    response = {}

    for data_key, data_value in data.items():
        response[data_key] = string_substitutions(data_value, substitutions, env_substitutions)

    return response
