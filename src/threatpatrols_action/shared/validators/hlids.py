from hlid import HLID


def validate_hlid(value: str, location_hint=None):
    try:
        assert HLID(value).age > 0
    except Exception:
        err = "Invalid hlid value supplied"
        if location_hint:
            err += f" in {location_hint}"
        err += "."
        raise ValueError(err)
