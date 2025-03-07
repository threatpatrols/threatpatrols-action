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

from pathlib import Path

from ... import action_models, config
from ...exceptions import ThreatPatrolsException
from ..lib.state import get_state_handler

state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
)

from ..models.callback import (
    CallbackHttp,
    CallbackS3Put,
    CallbackSend,
    CallbackSlack,
    CallbackSmtp,
    CallbackThreatpatrols,
)


async def get_callback_send_data(send: CallbackSend, state_key: str, summary_model):
    return await get_callback_send_filepath(send, state_key, summary_model, _return_data=True)


async def get_callback_send_filepath(send: CallbackSend, state_key: str, summary_model, _return_data=False):

    if not send:
        return None

    content = None
    extension = "summary"
    if send == CallbackSend.SUMMARY:
        try:
            summary_data = await state_handler.load_state(key=state_key, extension=extension)
        except ThreatPatrolsException:
            summary_data = None
        if not summary_data:
            output_data = await state_handler.load_state(key=state_key, extension="out")
            summary_data = summary_model(**output_data).model_dump()
            await state_handler.save_state(key=state_key, data=summary_data, extension=extension)
    elif send == CallbackSend.OUTPUT:
        extension = "out"
    elif send == CallbackSend.INPUT:
        extension = "in"
    else:
        if send.value not in action_models.ActionCallbackSendsMap.keys():
            raise ThreatPatrolsException(f"Unsupported CallbackSend {send=}")

        extension = str(send.value).lower()
        content = action_models.ActionCallbackSendsMap[send.value](
            await state_handler.load_state(key=state_key, extension="out"),
            await state_handler.load_state(key=state_key, extension="in"),
        )
        if content:
            await state_handler.save_content(key=state_key, content=content, extension=extension)

    if _return_data and content:
        return content
    elif _return_data:
        return await state_handler.load_state(key=state_key, extension=extension)

    return Path(state_handler.key_file(key=state_key, extension=extension))


from .http import http_callback
from .s3put import s3put_callback
from .slack import slack_callback
from .smtp import smtp_callback
from .threatpatrols import threatpatrols_callback

callback_function_map = {
    "http": http_callback,
    "s3put": s3put_callback,
    "slack": slack_callback,
    "smtp": smtp_callback,
    "threatpatrols": threatpatrols_callback,
}

callback_model_map = {
    "http": CallbackHttp,
    "s3put": CallbackS3Put,
    "slack": CallbackSlack,
    "smtp": CallbackSmtp,
    "threatpatrols": CallbackThreatpatrols,
}
