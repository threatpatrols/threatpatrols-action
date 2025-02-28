import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from boto3 import client as boto3client
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError
from botocore.session import get_session

from ... import config
from ...exceptions import ThreatPatrolsException
from ..lib.hash import hash_of_file

logger = logging.getLogger(config.LOGGER_NAME)


def s3put(file: Path, url: str) -> dict[str, Any]:
    logger.debug(f"s3put(file={file.name}, {url=})")

    if not url:
        raise ThreatPatrolsException("Empty <url> supplied, must provide a value.")

    if not Path(file).is_file():
        raise ThreatPatrolsException("Unable to locate file to upload for S3 action.")

    session = get_session()

    try:
        # let boto3 do its thing to acquire appropriate credentials from file(s) or environment variable(s)
        credentials = session.get_credentials().get_frozen_credentials()
    except AttributeError:
        _msg = "Unable to locate S3 credentials.  Use any credential method supported by boto3."
        raise ThreatPatrolsException(_msg)

    endpoint_url, bucket, object_key = _parse_url(url)

    s3boto3client = boto3client(
        "s3",
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
        endpoint_url=endpoint_url,
        config=BotoConfig(signature_version="s3v4"),
    )

    logger.debug(f"Sending {file.name!r} to {object_key!r}")

    try:
        with open(file, "rb") as f:
            response = s3boto3client.put_object(
                Body=f,
                Bucket=bucket,
                Key=object_key,
                ContentLength=Path(file).stat().st_size,
                ContentMD5=hash_of_file(file, hash_method="md5", base64_encoded=True),
            )
    except BotoCoreError as e:
        raise ThreatPatrolsException(e)  # Crimes!

    return response


def _parse_url(url: str) -> tuple[str | None, str, str]:
    parsed = urlparse(url)

    if parsed.scheme in ("s3", "aws"):
        endpoint_url = None
        bucket = parsed.netloc
        key = parsed.path.strip("/")
    elif parsed.scheme in ("gs", "gcp", "google"):
        endpoint_url = "https://storage.googleapis.com"
        bucket = parsed.netloc
        key = parsed.path.strip("/")
    elif parsed.scheme in ("http", "https"):
        endpoint_url = f"{parsed.scheme}://{parsed.netloc}"
        bucket = parsed.path.strip("/").split("/")[0]
        key = "/".join(parsed.path.strip("/").split("/")[1:])
    else:
        raise ThreatPatrolsException(
            "S3 url supplied does not start with a supported <provider>, must start with 's3://' for "
            "AWS, 'gs://' for GCP or 'http[s]://' for other S3 compatible endpoints.  See docs for detail."
        )

    return endpoint_url, bucket, key
