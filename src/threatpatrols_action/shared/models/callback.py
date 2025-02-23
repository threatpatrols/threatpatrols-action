from . import BaseModelPrivateHandler


class Callback(BaseModelPrivateHandler):
    action_name: str
    action_call_id: str
    action_task_id: str


class CallbackHttp(Callback):
    url: str
    method: str
    data: str
    headers: dict
    proxy: str


class CallbackS3(Callback):
    bucket: str
    object_key: str
    object_data_b64: str


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
