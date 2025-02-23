import os.path
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from boto3 import client as boto3client
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError
from botocore.session import get_session

from .. import constants
from ..exceptions import ThreatPatrolsRunnerException
from ..lib.hash import hash_of_file
from ..lib.logger import logger_get

logger = logger_get(constants.LOGGER_NAME)


def send_s3_boto3(file: Path, uri: str) -> tuple[dict[str, Any], Path]:
    logger.debug(f"send_s3_s3put(file={str(file)}, {uri=})")

    if not uri:
        raise ThreatPatrolsRunnerException("Empty <uri> supplied, must provide a value in --send-s3")

    if not os.path.isfile(file):
        raise ThreatPatrolsRunnerException("Unable to locate file to upload for --send-s3 S3 action.")

    session = get_session()

    try:
        # let boto3 do its thing to acquire appropriate credentials from file(s) or environment variable(s)
        credentials = session.get_credentials().get_frozen_credentials()
    except AttributeError:
        _msg = "Unable to locate S3 credentials for --send-s3.  Use any credential method supported by boto3."
        raise ThreatPatrolsRunnerException(_msg)

    endpoint_url, bucket, key_prefix = _parse_uri(uri)

    s3boto3client = boto3client(
        "s3",
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
        endpoint_url=endpoint_url,
        config=BotoConfig(signature_version="s3v4"),
    )

    object_key = f"{key_prefix.strip('/')}/{file.name}"
    logger.debug(f"Sending {file.name!r} to {object_key!r}")

    try:
        with open(file, "rb") as f:
            response = s3boto3client.put_object(
                Body=f,
                Bucket=bucket,
                Key=object_key,
                ContentLength=os.path.getsize(file),
                ContentMD5=hash_of_file(file, hash_method="md5", base64_encoded=True),
            )
    except BotoCoreError as e:
        raise ThreatPatrolsRunnerException(str(e))

    return response, Path(object_key)


def _parse_uri(uri: str) -> tuple[str | None, str, str]:
    parsed = urlparse(uri)

    if parsed.scheme in ("s3", "aws"):
        endpoint_url = None
        bucket = parsed.netloc
        key_prefix = parsed.path.strip("/")
    elif parsed.scheme in ("gs", "gcp", "google"):
        endpoint_url = "https://storage.googleapis.com"
        bucket = parsed.netloc
        key_prefix = parsed.path.strip("/")
    elif parsed.scheme in ("http", "https"):
        endpoint_url = f"{parsed.scheme}://{parsed.netloc}"
        bucket = parsed.path.strip("/").split("/")[0]
        key_prefix = "/".join(parsed.path.strip("/").split("/")[1:])
    else:
        raise ThreatPatrolsRunnerException(
            "Uri supplied in --send-s3 does not start with a supported <provider>, must start with 's3://' for "
            "AWS, 'gs://' for GCP or 'http[s]://' for other S3 compatible endpoints.  See docs for detail."
        )

    return endpoint_url, bucket, key_prefix
