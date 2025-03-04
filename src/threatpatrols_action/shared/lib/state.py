import asyncio
import datetime
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from random import randrange
from typing import Any, Optional
from uuid import uuid4

import aiofiles
from hlid import HLID

from ... import config
from ...exceptions import ThreatPatrolsException
from .jsonable import jsonable_encoder

DEFAULT_STATE_FILESYSTEM_TTL_SECONDS = 3600 * 8
DEFAULT_STATE_FILESYSTEM_MAX_WAIT_SECONDS = 30
DEFAULT_STATE_FILESYSTEM_SLEEP_WAIT_SECONDS = 0.1
DEFAULT_STATE_FILESYSTEM_MAX_RETRIES = 8
DEFAULT_STATE_FILESYSTEM_ROOT_PATH = "/tmp/tpas"

logger = logging.getLogger(config.LOGGER_NAME)


class StateHandlerFilesystem:

    state_ttl_seconds: int
    max_wait_seconds: int
    sleep_wait_seconds: float
    max_retries: int = 8
    root_path: Path

    def __init__(
        self,
        state_ttl_seconds: int = DEFAULT_STATE_FILESYSTEM_TTL_SECONDS,
        max_wait_seconds: int = DEFAULT_STATE_FILESYSTEM_MAX_WAIT_SECONDS,
        sleep_wait_seconds: float = DEFAULT_STATE_FILESYSTEM_SLEEP_WAIT_SECONDS,
        max_retries: int = DEFAULT_STATE_FILESYSTEM_MAX_RETRIES,
        root_path: Path = DEFAULT_STATE_FILESYSTEM_ROOT_PATH,
    ):
        self.state_ttl_seconds = state_ttl_seconds
        self.max_wait_seconds = max_wait_seconds
        self.sleep_wait_seconds = sleep_wait_seconds
        self.max_retries = max_retries

        self.root_path = Path(root_path)
        if not self.root_path.exists():
            self.root_path.mkdir(parents=True, exist_ok=True)

    def key_file(self, key: str, extension: str, mkdir_missing=False) -> Path:
        full_path = self.root_path / Path(key)
        if mkdir_missing and not full_path.parent.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
        return Path(f"{str(full_path)}.{extension}")

    async def find_states(self, key: str, extension: str = "state", filter_expired_ttl: bool = False):
        results = []
        root_path = self.key_file(key=f"{key}/faux", extension="faux").parent
        logger.debug(f"StateHandlerFilesystem.find_states() {root_path=}")

        for path in sorted(root_path.rglob(f"*.{extension}.metadata"), reverse=True):
            path_hlid = path.name.split(".")[0]
            if (filter_expired_ttl is False and HLID(path_hlid).age < self.state_ttl_seconds) or (
                (filter_expired_ttl is True and HLID(path_hlid).age > self.state_ttl_seconds)
            ):
                state_key = f"{key}/" + path_hlid.split("-")[0] + "/" + path_hlid
                state = await self.load_state(key=state_key, extension=extension)
                results.append(state)
        return results

    async def load_state(self, key: str, extension: str = "state", _retry_count: int = 0):
        _, data = await self.load_content(key=key, extension=extension, _retry_count=_retry_count)
        if not data:
            return None
        return json.loads(data)

    async def load_content(self, key: str, extension: str = "data", _retry_count: int = 0) -> tuple[dict, bytes]:

        data_file = self.key_file(key=key, extension=extension)
        metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        if _retry_count > self.max_retries:
            raise ThreatPatrolsException(f"Failed to load_content() after {self.max_retries} retries. {data_file=}")

        if not data_file.exists():
            raise ThreatPatrolsException(f"State file {data_file} not found.")

        if not metadata_file.exists():
            await self.jittery_sleep()
            return await self.load_content(key=key, extension=extension, _retry_count=_retry_count + 1)

        async with aiofiles.open(data_file, "rb") as f:
            data = await f.read()

        try:
            async with aiofiles.open(metadata_file, "r") as f:
                meta_data = json.loads(await f.read())
        except json.decoder.JSONDecodeError as e:
            logger.warning(str(e))
            if _retry_count > 2:
                logger.warning(f"Unable to JSON decode {metadata_file=}")
                return {}, b""
            await self.jittery_sleep()
            return await self.load_content(key=key, extension=extension, _retry_count=_retry_count + 1)

        if meta_data.get("key", "") != key:
            raise ThreatPatrolsException(f"Failed to read state mismatch {key=} in metadata file.")

        if int(meta_data.get("bytes", "0")) != len(data):
            if _retry_count > 2:
                logger.warning(f"Unable to locate 'bytes' in {metadata_file=}")
                return {}, b""
            await self.jittery_sleep()
            return await self.load_content(key=key, extension=extension, _retry_count=_retry_count + 1)

        if meta_data.get("sha256", "") != hashlib.sha256(data).hexdigest():
            if _retry_count > 2:
                logger.warning(f"Unable to locate 'sha256' in {metadata_file=}")
                return {}, b""
            await self.jittery_sleep()
            return await self.load_content(key=key, extension=extension, _retry_count=_retry_count + 1)

        logger.debug(f"StateHandlerFilesystem.load_content() {data_file=}")
        return meta_data, data

    async def save_content(
        self, key: str, content: bytes, filename: str | None = None, extension: str = "data"
    ) -> Path:
        data_file = self.key_file(key=key, extension=extension, mkdir_missing=True)
        metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        if not isinstance(content, bytes):
            raise ThreatPatrolsException(f"Content for save_content() must be bytes, {type(content)} supplied.")

        content_metadata = {
            "key": key,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "timestamp": str(datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0).isoformat()),
        }
        if filename:
            content_metadata["filename"] = filename

        metadata = json.dumps(content_metadata, separators=(",", ":"))

        writelock_file = await self.writelock_state(key=key, extension=extension)
        async with aiofiles.open(data_file, "wb") as fw1:
            await fw1.write(content)
        async with aiofiles.open(metadata_file, "w") as fw2:
            await fw2.write(metadata)

        try:
            os.unlink(writelock_file)
        except FileNotFoundError:
            pass

        logger.debug(f"StateHandlerFilesystem.save_content() {data_file=}")
        return data_file

    async def save_state(self, key: str, data: Any, extension="state") -> Path:
        if not isinstance(data, (dict, list)):
            raise ThreatPatrolsException(f"Content for save_state() must be dict|list, {type(data)} supplied.")
        state_data = json.dumps(jsonable_encoder(data), separators=(",", ":")).encode("utf8")
        return await self.save_content(key=key, content=state_data, extension=extension)

    async def remove_state(self, key: str, extension: str = "state") -> Path:
        state_data_file = self.key_file(key=key, extension=extension, mkdir_missing=True)
        state_metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        state_writelock_file = await self.writelock_state(key=key, extension=extension)
        for unlink_file in [state_data_file, state_metadata_file, state_writelock_file]:
            try:
                os.unlink(unlink_file)
            except FileNotFoundError:
                pass

        logger.debug(f"StateHandlerFilesystem.remove_state() {state_data_file=}")
        return state_data_file

    async def writelock_state(self, key: str, extension: str, _retry_count=0) -> Path:

        if _retry_count > self.max_retries:
            raise ThreatPatrolsException(f"Failed to create writelock after {self.max_retries} retries.")

        writelock_file = self.key_file(key=key, extension=f"{extension}.writelock")
        writelock_content = json.dumps({"key": key, "nonce": uuid4().hex})
        max_wait_until = time.time() + self.max_wait_seconds

        while writelock_file.exists():
            await self.jittery_sleep()
            if time.time() > max_wait_until:
                raise ThreatPatrolsException(f"Failed to acquire writelock after {self.max_wait_seconds} seconds.")

        with open(writelock_file, "w") as fw:
            fw.write(writelock_content)
        try:
            async with aiofiles.open(writelock_file, "r") as fr:
                if await fr.read() != writelock_content:
                    await self.jittery_sleep()
                    return await self.writelock_state(key=key, extension=extension, _retry_count=_retry_count + 1)
        except FileNotFoundError:
            await self.jittery_sleep()
            return await self.writelock_state(key=key, extension=extension, _retry_count=_retry_count + 1)

        logger.debug(f"StateHandlerFilesystem.writelock_state() {writelock_file=}")
        return writelock_file

    async def jittery_sleep(self, sleep_seconds: Optional[float] = None, jitter_p: float = 0.75):
        if not sleep_seconds:
            sleep_seconds = self.sleep_wait_seconds
        sleep_milliseconds = int(sleep_seconds * 1000)
        jitter_half_milliseconds = int((sleep_seconds * jitter_p) / 2 * 1000)
        sleep_ms = randrange(
            start=sleep_milliseconds - jitter_half_milliseconds, stop=sleep_milliseconds + jitter_half_milliseconds
        )
        logger.debug(f"StateHandlerFilesystem.jittery_sleep() {sleep_ms=}")
        await asyncio.sleep(sleep_ms / 1000)


def get_state_handler(
    method: str,
    method_params: Optional[dict[str, str]] = None,
    state_ttl_seconds: Optional[int] = None,
) -> StateHandlerFilesystem:

    if not method_params:
        method_params = {}

    if method == "filesystem":
        return StateHandlerFilesystem(**{**method_params, **{"state_ttl_seconds": state_ttl_seconds}})
    # elif method == "redis":
    #     return StateHandlerRedis(**{**method_params, **{"state_ttl_seconds": state_ttl_seconds}})

    raise ThreatPatrolsException("StateHandler only supports 'filesystem' method at this time.")
