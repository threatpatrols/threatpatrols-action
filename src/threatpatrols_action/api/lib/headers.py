from copy import copy

from fastapi import Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from threatpatrols_action import config


def get_request_id_header(request_id: str = Header(None, include_in_schema=False)):
    if not request_id:
        raise HTTPException(status_code=400, detail="Missing Request-ID header.")
    return request_id


def get_validated_api_key(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    api_key = __lookup_validated_bearer_token(bearer_token=credentials.credentials)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return api_key


def __lookup_validated_bearer_token(bearer_token: str):

    if not bearer_token:
        raise HTTPException(status_code=401, detail="Invalid bearer_token.")

    bearer_token_parts = bearer_token.split(".")
    if len(bearer_token_parts) < 2:
        raise HTTPException(status_code=401, detail="Invalid bearer_token components.")
    api_key_id = bearer_token_parts[0]
    api_key_secret = ".".join(bearer_token_parts[1:])

    if len(api_key_id) < 4 or len(api_key_secret) < 4:
        raise HTTPException(status_code=401, detail="Invalid bearer_token component formats.")

    #
    # NB: future improvement; lookup CREDENTIALS from something other than a static config file, eg Redis store.
    #

    if not config.CREDENTIALS:
        raise HTTPException(status_code=401, detail="No CREDENTIALS available; API authentication not possible.")

    if config.CREDENTIALS.get(api_key_id, {}).get("secret", "") == api_key_secret:
        credential = copy(config.CREDENTIALS.get(api_key_id))
        credential["id"] = api_key_id
        credential["secret"] = "****"
        return credential

    raise HTTPException(
        status_code=403,
        detail="API authentication not available with credentials supplied.",
    )
