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
import json
import logging
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ... import action_models, config
from ..lib.filemagic import guess_file_extension
from ..lib.jsonable import jsonable_encoder
from ..lib.substitutions import string_substitutions
from ..models import CallbackSend, CallbackSmtp
from ..validators.hlids import validate_hlid
from . import get_callback_send_data

logger = logging.getLogger(config.LOGGER_NAME)


async def smtp_callback(action_name: str, call_id: str, callback_config: dict):
    try:
        await smtp_callback_wrapper(action_name, call_id, callback_config)
    except Exception as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        # NB: do not terminate


async def smtp_callback_wrapper(action_name: str, call_id: str, callback_config: dict):

    # confirm input and output state is available
    validate_hlid(call_id, location_hint="smtp_callback_wrapper")
    state_key = "calls/" + call_id.split("-")[0] + "/" + call_id
    callback = CallbackSmtp(action_name=action_name, call_id=call_id, **callback_config)
    summary_data = await get_callback_send_data(
        send=CallbackSend.SUMMARY, state_key=state_key, summary_model=action_models.ActionItemSummary
    )

    message = MIMEMultipart()
    message["From"] = string_substitutions(callback.email_from, substitutions=summary_data)
    message["To"] = string_substitutions(callback.email_to, substitutions=summary_data)
    message["Subject"] = string_substitutions(callback.email_subject, substitutions=summary_data)

    # Email content
    message.attach(MIMEText(string_substitutions(callback.email_text, substitutions=summary_data), "plain"))

    # Email attachment
    if callback.send:
        send_data = await get_callback_send_data(
            send=callback.send,
            state_key=state_key,
            summary_model=action_models.ActionItemSummary,
        )

        if isinstance(send_data, (dict, list)):
            send_data = json.dumps(jsonable_encoder(send_data), indent="  ").encode()
            file_extension = "json"
        else:
            file_extension = guess_file_extension(send_data)

        part = MIMEBase("application", "octet-stream")
        part.set_payload(send_data)
        encoders.encode_base64(part)
        filename = f"{callback.send.value}.{file_extension}"
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        message.attach(part)

    # Send
    response = smtp_send_message(message=message.as_string(), callback=callback, substitutions_data=summary_data)

    log_message = (
        f"smtp callback: response={response} " f"action_name={callback.action_name} call_id={callback.call_id}"
    )
    logger.info(log_message)
    return


def smtp_send_message(message, callback, substitutions_data):

    smtp_host = string_substitutions(callback.smtp_host, substitutions=substitutions_data)
    smtp_port = int(string_substitutions(callback.smtp_port, substitutions=substitutions_data))
    smtp_user = string_substitutions(callback.smtp_user, substitutions=substitutions_data)
    smtp_pass = string_substitutions(callback.smtp_pass, substitutions=substitutions_data)
    email_from = string_substitutions(callback.email_from, substitutions=substitutions_data)
    email_to = string_substitutions(callback.email_to, substitutions=substitutions_data)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)  # Secure the connection
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.sendmail(email_from, email_to, message)

    return True
