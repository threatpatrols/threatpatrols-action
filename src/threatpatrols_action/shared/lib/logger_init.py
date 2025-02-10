import logging
from enum import IntEnum

try:
    from asgi_correlation_id import CorrelationIdFilter
except ImportError:
    CorrelationIdFilter = None


LOGGING_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
LOGGING_FORMAT_W_REQUEST_ID = "%(asctime)s | %(levelname)s | __name__ | %(correlation_id)s | %(message)s"
LOGGING_FORMAT_WO_REQUEST_ID = "%(asctime)s | %(levelname)s | __name__ | %(message)s"


class LogLevelEnum(IntEnum):
    all = 0
    debug = 10
    info = 20
    warning = 30
    error = 40
    critical = 50


def logger_get(name: str, loglevel="warning", logfile=None, with_request_id=True) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logging_level = getattr(LogLevelEnum, loglevel)
    logger.setLevel(logging_level.value)

    if with_request_id:
        logging_format = LOGGING_FORMAT_W_REQUEST_ID.replace("__name__", name)
    else:
        logging_format = LOGGING_FORMAT_WO_REQUEST_ID.replace("__name__", name)

    logging_formatter = logging.Formatter(fmt=logging_format, datefmt=LOGGING_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging_level.value)
    console_handler.setFormatter(logging_formatter)

    if with_request_id and CorrelationIdFilter:
        request_id = CorrelationIdFilter(uuid_length=24)
        console_handler.addFilter(request_id)

    logger.addHandler(console_handler)

    try:
        if logfile:
            file_handler = logging.FileHandler(filename=logfile)
            file_handler.setLevel(logging_level.value)
            file_handler.setFormatter(logging_formatter)
            logger.addHandler(file_handler)
    except (FileNotFoundError, PermissionError):
        raise PermissionError(f"Unable to write to logfile at: {logfile}")

    return logger


def logger_setlevel(name: str, loglevel: str) -> None:
    logger = logging.getLogger(name)
    logging_level = getattr(LogLevelEnum, loglevel)

    logger.setLevel(logging_level.value)
    for handler in logger.handlers:
        handler.setLevel(logging_level.value)

    return None
