import logging

import httpx

from threatpatrols_action import config
from threatpatrols_action.exceptions import ThreatPatrolsException

TITLE = config.TITLE
VERSION = config.VERSION

logger = logging.getLogger(config.LOGGER_NAME)


def log_debug_request(request):
    logger.debug(f"request: {request.method} {request.url}")
    if "_content" in vars(request) and request._content:
        logger.debug(f"request-data: {request._content}")


def log_debug_response(response):
    logger.debug(f"response: {response.request.method} {response.request.url}  | status:{response.status_code}")


class HttpClient:
    request_timeout: int
    verify: bool
    debug: bool

    def __init__(self, request_timeout=10, verify=True, debug=False):
        self.request_timeout = request_timeout
        self.verify = verify
        self.debug = debug

    @property
    def user_agent(self) -> str:
        return f"{TITLE.replace(' ', '')}/{VERSION}"

    def get(self, **kwargs):
        return self.request(method="GET", **kwargs)

    def post(self, **kwargs):
        return self.request(method="POST", **kwargs)

    def patch(self, **kwargs):
        return self.request(method="PATCH", **kwargs)

    def request(self, **kwargs) -> httpx.Response:
        event_hooks = {"request": [], "response": []}
        if self.debug:
            event_hooks["request"].append(log_debug_request)
            event_hooks["response"].append(log_debug_response)

        if "params" in kwargs and isinstance(kwargs["params"], dict):
            kwargs["params"] = {k: v for (k, v) in kwargs["params"].items() if v or isinstance(v, int)}

        httpx_client = {
            "headers": {"User-Agent": self.user_agent},
            "http2": False,
            "timeout": self.request_timeout,
            "trust_env": False,
            "verify": self.verify,
            "event_hooks": event_hooks,
        }

        if "url" not in kwargs:
            raise ThreatPatrolsException("Parameter 'url' for request() not present")

        try:
            with httpx.Client(**httpx_client) as client:
                request = client.build_request(**kwargs)
                response = client.send(request=request)
        except (httpx.ConnectError, httpx.RemoteProtocolError):
            raise ThreatPatrolsException(f"Unable to establish connection to {kwargs['url']!r}")

        return response
