from typing import Any, get_args


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
