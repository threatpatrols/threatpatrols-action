#
# Copyright [2025] Threat Patrols Pty Ltd (https://www.threatpatrols.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
from typing import Any, Optional

import httpx

from ... import config
from ...exceptions import ThreatPatrolsException

logger = logging.getLogger(config.LOGGER_NAME)


async def httpx_debug_request(request):
    logger.debug(f"request: {request.method} {request.url}")
    if "_content" in vars(request) and request._content:  # noqa
        logger.debug(f"request-data: {request._content}")  # noqa


async def httpx_debug_response(response):
    logger.debug(
        f"response: {response.request.method} {response.request.url} "
        f"{response.status_code=} {response.http_version=} {response.headers=}"
    )


class HttpClient:
    proxy: Optional[str]
    verify: bool
    http2: bool
    request_timeout: int  # seconds
    debug: bool

    def __init__(
        self,
        proxy: Optional[str] = None,
        verify: bool = True,
        http2: bool = False,
        request_timeout: int = 15,
        debug: bool = False,
    ):
        self.proxy = proxy
        self.verify = verify
        self.http2 = http2
        self.request_timeout = request_timeout
        self.debug = debug

    @property
    def user_agent(self) -> str:
        return f"{config.ACTION_NAME}/{config.VERSION}"

    async def get(self, **kwargs):
        return await self.request(method="GET", **kwargs)

    async def post(self, **kwargs):
        return await self.request(method="POST", **kwargs)

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        data: Any = None,
        follow_redirects: bool = True,
        max_retries: int = 3,
        __attempt: int = 0,
    ):
        event_hooks = {}
        if self.debug:
            event_hooks["request"] = [httpx_debug_request]
            event_hooks["response"] = [httpx_debug_response]

        if not headers:
            headers = {"User-Agent": self.user_agent}
        else:
            headers = {**{"User-Agent": self.user_agent}, **headers}

        httpx_client = {
            "headers": headers,
            "http2": self.http2,
            "timeout": self.request_timeout,
            "verify": self.verify,
            "follow_redirects": follow_redirects,
            "trust_env": False,
        }

        if self.proxy:
            httpx_client["proxy"] = self.proxy

        if event_hooks:
            httpx_client["event_hooks"] = event_hooks

        async with httpx.AsyncClient(**httpx_client) as client:
            __attempt += 1
            logger.debug(f"Request [attempt:{__attempt}/{max_retries}] {method} {url!r}")
            request = client.build_request(method=method, url=url, data=data)
            try:
                response = await client.send(request=request, stream=True)
            except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.HTTPError):
                logger.warning(f"Request [{__attempt} of {max_retries}] failed for {request.method!r} {url!r}")
                if __attempt < max_retries:
                    return await self.request(method, url, headers, data, follow_redirects, max_retries, __attempt)
                raise ThreatPatrolsException(f"Request failed after {__attempt} retries: {url!r}")

            response.binary = b"".join([part async for part in response.aiter_raw()])

        return response
