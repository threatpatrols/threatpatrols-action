from typing import Optional

from . import PrivateHandleBaseModel


class Callback(PrivateHandleBaseModel):
    action_name: str
    action_call_id: str
    action_task_id: str
    _tags: Optional[dict[str, str]] = None  # TODO: replace via PrivateHandleBaseModel


class CallbackHttp(Callback):
    url: str
    method: str
    data: str
    headers: dict


class CallbackSmtp(Callback):
    email_to: str
    email_from: str
    subject: str
    body_text: str
    body_html: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
