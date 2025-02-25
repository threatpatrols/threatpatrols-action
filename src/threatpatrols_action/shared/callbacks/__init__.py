from ... import config
from ..lib.state import get_state_handler

state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
)

from ..models.callback import CallbackHttp, CallbackS3Put, CallbackSlack, CallbackSmtp, CallbackThreatpatrols
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
