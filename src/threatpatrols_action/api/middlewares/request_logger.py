import logging
import time

from fastapi import Request

from threatpatrols_action import config
from threatpatrols_action.shared.lib.validators import is_user_agent


def add_request_logger_middleware(app):
    logger = logging.getLogger(config.LOGGER_NAME)

    @app.middleware("http")
    async def log_requests(request: Request, func):
        client_ipaddr, client_ipaddr_source = get_request_ipaddr(request)

        user_agent = request.headers.get("user-agent", "Unknown (User-Agent not set)")
        if not is_user_agent(user_agent):
            user_agent = "Invalid (User-Agent non-permitted characters)"

        logger.info(
            f"log='request' method={request.method!r} path={request.url.path!r} ipaddr={client_ipaddr!r} "
            f"ipaddr_source={client_ipaddr_source!r} user_agent={user_agent!r}"
        )

        start_time = time.perf_counter()
        response = await func(request)

        process_time = (time.perf_counter() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        logger.info(
            f"log='response' method={request.method!r} path={request.url.path!r} "
            f"completed_in={formatted_process_time}ms status_code={response.status_code}"
        )

        return response


def get_request_ipaddr(request: Request) -> tuple[str, str]:
    request_ipaddr = request.headers.get("cf-connecting-ip")
    if request_ipaddr:
        return request_ipaddr, "cf-connecting-ip"

    request_ipaddr = request.headers.get("x-real-ip")
    if request_ipaddr:
        return request_ipaddr, "x-real-ip"

    request_ipaddr = request.headers.get("x-forwarded-for")
    if request_ipaddr:
        return request_ipaddr.split(" ")[0], "x-forwarded-for"

    return str(request.client.host), "application"  # Request Client Host
