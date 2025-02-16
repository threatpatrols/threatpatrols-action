from copy import copy

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .. import config
from ..exceptions import ThreatPatrolsApiException


def __future_improvement_get_api_key(bearer_token: str):

    if not bearer_token:
        raise ThreatPatrolsApiException(status_code=401, detail="Invalid bearer_token.")

    bearer_token_parts = bearer_token.split(".")
    if len(bearer_token_parts) < 2:
        raise ThreatPatrolsApiException(status_code=401, detail="Invalid bearer_token components.")
    api_key_id = bearer_token_parts[0]
    api_key_secret = ".".join(bearer_token_parts[1:])

    if len(api_key_id) < 4 or len(api_key_secret) < 4:
        raise ThreatPatrolsApiException(status_code=401, detail="Invalid bearer_token component formats.")

    if not config.CREDENTIALS:
        raise ThreatPatrolsApiException(
            status_code=401, detail="No CREDENTIALS defined.", user_detail="API authentication not possible"
        )

    if config.CREDENTIALS.get(api_key_id, {}).get("secret", "") == api_key_secret:
        credential = copy(config.CREDENTIALS.get(api_key_id))
        credential["id"] = api_key_id
        credential["secret"] = "****"
        return credential


def validate_bearer_token(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    api_key = __future_improvement_get_api_key(bearer_token=credentials.credentials)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid token")
    return api_key


def validate_api_token():
    return Depends(validate_bearer_token)


def check_reserved_action_tags(tags):
    if not tags:
        return
    reserved_tag_keys = ["action_name", "api_key_id", "request_id", "task_id", "call_id", "call_timestamp"]
    for tag in tags.keys():
        if tag in reserved_tag_keys:
            raise ThreatPatrolsApiException(
                detail=f"Request contains reserved {tag=} key.", user_detail="secret: dQw4w9WgXcQ"  # seems appropriate
            )
