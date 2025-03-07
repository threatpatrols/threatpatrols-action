import mimetypes

import magic as filemagic


def guess_file_extension(content):
    if not isinstance(content, bytes):
        raise ValueError("Must provide bytes-type content in guess_file_extension()")

    mime_type = filemagic.from_buffer(content[0:2048], mime=True)
    if not mime_type:
        return "data"

    mime_type = mime_type.replace("x-script.", "x-")  # Urgh!
    kind = mimetypes.guess_extension(mime_type)

    if not kind:
        return "data"

    return kind.strip(".")
