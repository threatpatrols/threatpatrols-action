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
from ...shared.lib.s3put import s3put
from ..lib.casts import dict_to_flat_string
from ..lib.substitutions import string_substitutions
from ..models import CallbackS3Put, CallbackSend
from ..validators.hlids import validate_hlid
from . import get_callback_send_data, get_callback_send_filepath

logger = logging.getLogger(config.LOGGER_NAME)


async def s3put_callback(action_name: str, call_id: str, callback_config: dict):
    try:
        await s3put_callback_wrapper(action_name, call_id, callback_config)
    except Exception as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        # NB: do not terminate


async def s3put_callback_wrapper(action_name: str, call_id: str, callback_config: dict):

    # confirm input and output state is available
    validate_hlid(call_id, location_hint="s3put_callback_wrapper")
    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    callback = CallbackS3Put(action_name=action_name, call_id=call_id, **callback_config)
    summary_data = await get_callback_send_data(
        send=CallbackSend.SUMMARY, state_key=state_key, summary_model=action_models.ActionItemSummary
    )

    send_filepath = await get_callback_send_filepath(
        send=callback.send,
        state_key=state_key,
        summary_model=action_models.ActionItemSummary,
    )
    s3put_url = string_substitutions(callback.url, substitutions=summary_data)
    logger.info(f"S3Put target {s3put_url}")
    response = s3put(url=s3put_url, file=send_filepath)

    response_metadata = response.get("ResponseMetadata", {})
    logger.debug("s3put response headers: " + dict_to_flat_string(response_metadata.get("HTTPHeaders")))

    response_status_code = response_metadata.get("HTTPStatusCode", 500)
    log_message = (
        f"s3put callback: status_code={response_status_code} "
        f"action_name={callback.action_name} call_id={callback.call_id}"
    )

    if 299 >= response_status_code >= 200:
        logger.info(log_message)
        return

    logger.error(log_message)
