#
#  Copyright (c) 2025 Threat Patrols Pty Ltd <contact@threatpatrols.com>
#  See LICENSE.md for terms
#

import logging
import sys

from . import config

logger = logging.getLogger(config.LOGGER_NAME)


class ThreatPatrolsException(Exception):
    pass


class ThreatPatrolsApiException(Exception):
    """
    Threat Patrols System Exception
    :param detail: str : internal only exception detail used for logging
    :param data: str : internal only exception internal_detail used for logging
    :param user_detail: str : forms the user facing response message
    :param status_code: int : the HTTP response to be used for this response
    """

    def __init__(self, detail: str, data: str | None = None, user_detail: str | None = None, status_code: int = 500):
        self.detail = detail
        self.data = data
        self.user_detail = user_detail
        self.status_code = status_code


def generate_api_exception_response_handlers():
    """
    Create and return the set of api exception response handlers for the API
    """

    from fastapi import Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    async def threatpatrols_api_exception_handler(request: Request, exc: ThreatPatrolsApiException):
        """
        Handler for ThreatPatrolsApiException
        """

        status_code = int(exc.status_code)

        log_message = f"ThreatPatrolsApiException status_code={status_code} detail={str(exc.detail)!r}"
        if exc.user_detail:
            user_detail = str(exc.user_detail)
            log_message = f"{log_message} user_detail={user_detail!r}"
        else:
            user_detail = "Unable to complete the request; please try again later."

        if exc.data:
            log_message = f"{log_message} data={str(exc.data)!r}"

        logger.error(msg=log_message)

        if config.DEBUG:
            exception_info = sys.exc_info()
            if exception_info and len(exception_info) > 0:
                logger.error(msg="ThreatPatrolsApiException stacktrace_start", exc_info=True)
                logger.error(msg="ThreatPatrolsApiException stacktrace_end")

        return JSONResponse(
            status_code=status_code,
            content={"detail": user_detail},
        )

    async def fastapi_validation_error_handler(request: Request, exc: RequestValidationError):
        """
        Handler for FastAPI RequestValidationError (that inherits from Pydantic ValidationError)
        https://fastapi.tiangolo.com/tutorial/handling-errors/#requestvalidationerror-vs-validationerror
        """

        status_code = 422
        log_message = f"RequestValidationError status_code={status_code} detail={str(exc)!r}"
        logger.error(msg=log_message)

        try:
            user_detail = exc.args[0][0]["msg"]
            user_detail = user_detail.replace("','", "', '")  # NdJ: I'll pay for this some day.
        except:  # noqa
            user_detail = "Data validation error."

        try:
            user_detail += " (" + ": ".join(list(exc.args[0][0]["loc"])) + ")"
        except:  # noqa
            pass

        return JSONResponse(
            status_code=status_code,
            content={"detail": user_detail},
        )

    async def value_error_handler(request: Request, exc: ValueError):
        """
        Handler for ValueError
        """
        status_code = 422
        log_message = f"ValueError status_code={status_code} detail={str(exc)!r}"

        logger.error(msg=log_message)

        return JSONResponse(
            status_code=status_code,
            content={"detail": "Malformed data value error."},
        )

    return {
        ThreatPatrolsApiException: threatpatrols_api_exception_handler,
        RequestValidationError: fastapi_validation_error_handler,
        ValueError: value_error_handler,
    }
