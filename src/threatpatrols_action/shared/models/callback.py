from enum import Enum
from typing import Annotated, Optional

from pydantic import AfterValidator, AnyHttpUrl

from . import BaseModelPrivateHandler

HttpUrlString = Annotated[AnyHttpUrl, AfterValidator(lambda v: str(v))]


class CallbackSend(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    SUMMARY = "summary"


class CallbackHttpMethod(str, Enum):
    GET = "GET"
    PUT = "PUT"
    POST = "POST"


class Callback(BaseModelPrivateHandler):
    action_name: str
    call_id: str
    task_id: Optional[str] = None


class CallbackHttp(Callback):
    url: HttpUrlString
    method: CallbackHttpMethod = CallbackHttpMethod.POST
    data: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    proxy: Optional[str] = None
    verify: bool = True
    send: CallbackSend = CallbackSend.SUMMARY

    @property
    def name(self):
        return "http"

    def model_post_init(self, *args, **kwargs) -> None:
        super().model_post_init(*args, **kwargs)
        if self.method == CallbackHttpMethod.GET and self.data:
            raise ValueError("Cannot send 'data' in a HTTP.GET callback request.")


class CallbackS3Put(Callback):
    bucket: str
    object_key: str
    object_data_b64: str

    @property
    def name(self):
        return "s3put"


class CallbackSlack(Callback):

    @property
    def name(self):
        return "slack"


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

    @property
    def name(self):
        return "smtp"


class CallbackThreatpatrols(Callback):

    @property
    def name(self):
        return "threatpatrols"
