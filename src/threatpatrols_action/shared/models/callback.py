from enum import Enum
from typing import Annotated, Optional

from pydantic import AfterValidator, AnyHttpUrl, AnyUrl

from ... import action_models
from . import BaseModelPrivateHandler

HttpUrlString = Annotated[AnyHttpUrl, AfterValidator(lambda v: str(v))]
AnyUrlString = Annotated[AnyUrl, AfterValidator(lambda v: str(v))]

# NB: All Actions must provide action_models.ActionCallbackSendsMap even if an empty dict.
action_callback_sends = set(["input", "output", "summary"] + list(action_models.ActionCallbackSendsMap.keys()))
CallbackSend = Enum(  # type: ignore[misc]
    "CallbackSend",
    ((value.upper(), value.lower()) for value in action_callback_sends),
    type=str,
)


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
    url: str
    send: CallbackSend = CallbackSend.OUTPUT

    @property
    def name(self):
        return "s3put"


class CallbackSlack(Callback):
    token: str
    channel: str
    message: str
    send: Optional[CallbackSend] = None

    @property
    def name(self):
        return "slack"


class CallbackSmtp(Callback):
    smtp_host: str
    smtp_port: str
    smtp_user: str
    smtp_pass: str
    email_to: str
    email_from: str
    email_subject: str
    email_text: Optional[str] = None
    email_html: Optional[str] = None
    send: Optional[CallbackSend] = None

    @property
    def name(self):
        return "smtp"


class CallbackThreatpatrols(Callback):

    send: CallbackSend = CallbackSend.OUTPUT

    @property
    def name(self):
        return "threatpatrols"
