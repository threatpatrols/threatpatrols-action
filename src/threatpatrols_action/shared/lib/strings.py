def dict_as_string(data: dict) -> str:
    if not isinstance(data, dict):
        return ""
    return " ".join([f"{k}={data[k]!r}" for k in data.keys()])
