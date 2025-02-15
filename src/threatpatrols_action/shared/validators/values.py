import json
from typing import Any

# basic alphanumeric
ALPHANUMERIC_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
ALPHANUMERIC_LOWER_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"
ALPHANUMERIC_UPPER_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# various character sets
COMMON_CHARS = ALPHANUMERIC_CHARS + " ._-"
USER_AGENT_CHARS = ALPHANUMERIC_CHARS + " []()=:+_,-;/."


def string_scrub(value: Any, whitelist: str) -> str:
    """
    Return a string that only contains characters in the supplied whitelist set of characters
    """
    whitelist_chars_list = list(dict.fromkeys([*str(whitelist)]))
    return "".join(char for char in value if char in whitelist_chars_list)


def is_string_whitelist(value: Any, whitelist: str, min_length: int = 1, max_length: int = 256) -> bool:
    """
    Return True if the value is a string and only contains characters in the supplied set of characters
    """
    if not isinstance(value, str):
        return False
    if len(value) < min_length or len(value) > max_length:
        return False
    if value == string_scrub(value, whitelist=whitelist):
        return True
    return False


def raise_invalid_string_whitelist(value: Any, whitelist: str, min_length: int = 1, max_length: int = 256):
    if not is_string_whitelist(value, whitelist, min_length, max_length):
        raise ValueError("Invalid 'string' value; string_whitelist")


def is_string_alphanumeric(value: Any, min_length=1, max_length=256) -> bool:
    """
    Return True if the value only contains alphanumeric characters and length meets the mix/max limits
    """
    return is_string_whitelist(value=value, whitelist=ALPHANUMERIC_CHARS, min_length=min_length, max_length=max_length)


def raise_invalid_string_alphanumeric(value):
    if not is_string_alphanumeric(value):
        raise ValueError("Invalid 'string' value; string_alphanumeric")


def is_string_common(value: Any, min_length=1, max_length=256) -> bool:
    """
    Return True if the value only contains well-known common characters and length meets the mix/max limits
    """
    return is_string_whitelist(value=value, whitelist=COMMON_CHARS, min_length=min_length, max_length=max_length)


def raise_invalid_string_common(value, min_length=1, max_length=256):
    if not is_string_common(value, min_length, max_length):
        raise ValueError("Invalid 'string' value; string_common")


def is_string_json(value) -> bool:
    """
    Return True if the value is a string that can be loaded using json loads
    """
    if not isinstance(value, str):
        return False

    try:
        json.loads(value)
        return True
    except ValueError:
        pass

    return False


def raise_invalid_string_json(value):
    if not is_string_json(value):
        raise ValueError("Invalid 'json_string' value; string_json")


def is_user_agent(value) -> bool:
    return is_string_whitelist(value, whitelist=USER_AGENT_CHARS)


def raise_invalid_user_agent(value):
    if not is_user_agent(value):
        raise ValueError("Invalid 'user_agent' value; user_agent")
