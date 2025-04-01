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

from ... import action_models, config
from ..lib.http_client import HttpClient
from ..lib.substitutions import dict_value_substitutions, string_substitutions
from ..models import CallbackHttp, CallbackHttpMethod, CallbackSend
from ..validators.hlids import validate_hlid
from . import get_callback_send_data

logger = logging.getLogger(config.LOGGER_NAME)


async def http_callback(action_name: str, call_id: str, callback_config: dict):
    try:
        await http_callback_wrapper(action_name, call_id, callback_config)
    except Exception as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        # NB: do not terminate


async def http_callback_wrapper(action_name: str, call_id: str, callback_config: dict):
    # confirm input and output state is available
    validate_hlid(call_id, location_hint="http_callback_wrapper")
    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    callback = CallbackHttp(action_name=action_name, call_id=call_id, **callback_config)
    summary_data = await get_callback_send_data(
        send=CallbackSend.SUMMARY, state_key=state_key, summary_model=action_models.ActionItemSummary
    )

    request_args = {
        "method": callback.method.value,
        "url": string_substitutions(callback.url, substitutions=summary_data),
        "headers": dict_value_substitutions(callback.headers, substitutions=summary_data),
    }

    if not callback.method != CallbackHttpMethod.GET:
        request_args["data"] = await get_callback_send_data(
            send=callback.send,
            state_key=state_key,
            summary_model=action_models.ActionItemSummary,
        )

    http_client = HttpClient(proxy=callback.proxy, verify=callback.verify)
    response = await http_client.request(**request_args)

    log_message = (
        f"HTTP callback: status_code={response.status_code} "
        f"action_name={callback.action_name} call_id={callback.call_id}"
    )

    if 299 >= response.status_code >= 200:
        logger.info(log_message)
        return

    logger.error(log_message)
