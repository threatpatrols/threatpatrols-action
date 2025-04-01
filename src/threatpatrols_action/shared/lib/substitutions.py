#
# Copyright [2025] Threat Patrols Pty Ltd (https://www.threatpatrols.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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

    # create undefined replacements
    # ===
    for string_token in [tkn.strip() for _, tkn, _, _ in Formatter().parse(value) if tkn]:
        if string_token not in replacements.keys():
            replacements[string_token] = ""  # empty string
            logger.warning(f"Substitution data token={string_token!r} not available for replacement in {value!r}")

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
