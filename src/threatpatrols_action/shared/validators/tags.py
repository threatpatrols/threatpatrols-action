from ... import config

USER_TAG_MAX_COUNT = config.USER_TAG_MAX_COUNT
USER_TAG_MAX_KEY_LENGTH = config.USER_TAG_MAX_KEY_LENGTH
USER_TAG_MAX_VALUE_LENGTH = config.USER_TAG_MAX_VALUE_LENGTH


def validate_action_tags(tags):
    if len(tags) > USER_TAG_MAX_COUNT:
        raise ValueError(f"User supplied tags exceeds {USER_TAG_MAX_COUNT} limit per action request")

    if any(len(str(v)) > USER_TAG_MAX_VALUE_LENGTH for v in tags.values()):
        raise ValueError(f"User supplied tag-value exceeds {USER_TAG_MAX_VALUE_LENGTH} length in action request")

    if any(len(str(k)) > USER_TAG_MAX_KEY_LENGTH for k in tags.keys()):
        raise ValueError(f"User supplied tag-key exceeds {USER_TAG_MAX_KEY_LENGTH} length in action request")


def validate_reserved_action_tags(tags):
    if not tags:
        return
    reserved_tag_keys = ["action_name", "api_key_id", "request_id", "task_id", "call_id", "call_timestamp"]
    for tag in tags.keys():
        if tag in reserved_tag_keys:
            raise ValueError(f"Request contains reserved {tag=} key, review secret value: dQw4w9WgXcQ")  # Rickroll
