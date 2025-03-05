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

from collections.abc import MutableMapping
from typing import Any, get_args


def flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    return dict(_flatten_dict_gen(d, parent_key, sep))


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def dict_to_flat_string(data: dict) -> str:
    if not isinstance(data, dict):
        return ""  # type: ignore
    return " ".join([f"{k}={data[k]!r}" for k in data.keys()])


def list_to_dict(data: list) -> dict:
    if not data:
        return {}

    if not isinstance(data, list):
        raise ValueError("Value must be list type with str-type items in '<key>:<value>' format for dict-type cast.")

    replacement = {}
    for item in data:
        if not isinstance(item, str):
            raise ValueError("List value must be str-type in '<key>:<value>' format for dict-type cast.")

        if ":" not in item:
            raise ValueError("List item must be in '<key>:<value>' format for dict-type cast.")

        item_key, item_value = item.split(":", maxsplit=1)
        replacement[item_key] = item_value

    return replacement


def str_to_int(data: str) -> int:
    try:
        result = int(data)  # type: ignore
    except Exception:
        raise ValueError("Value does not cast into int-type")
    return result


def str_to_float(data: str) -> float:
    try:
        result = float(data)  # type: ignore
    except Exception:
        raise ValueError("Value does not cast into float-type")
    return result


def annotation_to_type(annotation) -> Any:
    if "typing.Optional" in str(annotation):
        return ([x for x in get_args(annotation) if x is not None])[0]
    return annotation


def annotation_to_type_name(annotation) -> str:
    return annotation_to_type(annotation).__name__


def annotation_is_optional(annotation) -> bool:
    if "typing.Optional" in str(annotation):
        return True
    return False
