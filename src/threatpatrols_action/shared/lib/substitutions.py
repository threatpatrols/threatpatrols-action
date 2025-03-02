import logging
import os
from string import Formatter
from typing import Optional

from ... import config
from ..lib.casts import flatten_dict

logger = logging.getLogger(config.LOGGER_NAME)


def string_substitutions(value: str, substitutions: Optional[dict] = None, env_substitutions: bool = True):

    if not value:
        return value

    replacements = {}

    # collect env replacements
    # ===
    if env_substitutions:
        for env_key, env_value in os.environ.items():
            token = "${" + env_key + "}"
            if token in value:
                replacements[env_key] = env_value
                value = value.replace(token, token.lstrip("$"))

    # collect substitution replacements
    # ===
    if isinstance(substitutions, dict):
        for substitution_key, substitution_value in flatten_dict(substitutions).items():
            token_key = substitution_key.replace("_tags.", "tag.", 1)
            token = "{" + token_key + "}"

            if token in value:
                replacements[token_key] = substitution_value

            # # special case: call_id/task_id
            # if token_key in ("task_id", "call_id") or token_key.endswith((".task_id", ".call_id")):
            #     x_token_key = f"{token_key}_prefix"
            #     if "{" + x_token_key + "}" in value:
            #         replacements[x_token_key] = substitution_value.split("-")[0]
            #
            # # special case: action_name
            # if token_key == "action_name" or token_key.endswith(".action_name"):
            #     x_token_key = token_key.replace("action_name", "action_title")  # sketchy
            #     if "{" + x_token_key + "}" in value:
            #         replacements[x_token_key] = substitution_value.replace("-", " ").replace("_", " ").title()

    # create undefined replacements
    # ===
    for string_token in [tkn.strip() for _, tkn, _, _ in Formatter().parse(value) if tkn]:
        if string_token not in replacements.keys():
            replacements[string_token] = "{" + string_token + "}"

    # perform replacements
    # ===
    for key in [tkn.strip() for _, tkn, _, _ in Formatter().parse(value) if tkn]:
        value = value.replace("{" + key + "}", str(replacements.get(key)))

    return value


def dict_value_substitutions(
    data: dict, substitutions: Optional[dict] = None, env_substitutions: bool = True
) -> dict[str, str]:
    if not data:
        return data
    response = {}
    for data_key, data_value in data.items():
        response[data_key] = string_substitutions(data_value, substitutions, env_substitutions)
    return response


def list_value_substitutions(
    data: list, substitutions: Optional[dict] = None, env_substitutions: bool = True
) -> list[str]:
    if not data:
        return data
    response = []
    for data_value in data:
        response.append(string_substitutions(data_value, substitutions, env_substitutions))
    return response
