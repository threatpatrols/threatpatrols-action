import logging

from ... import config

logger = logging.getLogger(config.LOGGER_NAME)


def string_substitutions(value: str, substitutions: dict):
    if not substitutions:
        return value
    if "task_id" in substitutions.keys():
        substitutions["task_id_prefix"] = substitutions.get("task_id").split("-")[0]
    if "call_id" in substitutions.keys():
        substitutions["call_id_prefix"] = substitutions.get("call_id").split("-")[0]
    replacements = {}
    for tag_key, tag_value in substitutions.items():
        if "{" + tag_key + "}" in value.replace(" ", ""):
            replacements[tag_key] = tag_value
    try:
        return value.format(**replacements)
    except KeyError as e:
        logger.warning(f"Unknown replacement token {str(e)} encountered, token will not be replaced.")
        return value
