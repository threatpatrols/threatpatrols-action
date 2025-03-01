import asyncio
import datetime
import hashlib
import json
import os
import time
from pathlib import Path
from random import randrange
from typing import Any, Optional
from uuid import uuid4

import aiofiles
from hlid import HLID

from ...exceptions import ThreatPatrolsException
from .jsonable import jsonable_encoder

DEFAULT_STATE_FILESYSTEM_TTL_SECONDS = 3600 * 8
DEFAULT_STATE_FILESYSTEM_MAX_WAIT_SECONDS = 30
DEFAULT_STATE_FILESYSTEM_SLEEP_WAIT_SECONDS = 0.25
DEFAULT_STATE_FILESYSTEM_MAX_RETRIES = 8
DEFAULT_STATE_FILESYSTEM_ROOT_PATH = "/tmp/tpas"


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

    async def find_states(self, key: str, extension: str = "data", filter_expired_ttl: bool = False):
        results = []
        root_path = self.key_file(key=f"{key}/faux", extension="faux").parent
        for path in sorted(root_path.rglob(f"*.{extension}.metadata"), reverse=True):
            path_hlid = path.name.split(".")[0]
            if (filter_expired_ttl is False and HLID(path_hlid).age < self.state_ttl_seconds) or (
                (filter_expired_ttl is True and HLID(path_hlid).age > self.state_ttl_seconds)
            ):
                state_key = f"{key}/" + path_hlid.split("-")[0] + "/" + path_hlid
                state = await self.load_state(key=state_key, extension=extension)
                results.append(state)
        return results

    async def load_state(self, key: str, extension: str = "data", _retry_count=0):

        if _retry_count > self.max_retries:
            raise ThreatPatrolsException(f"Failed to read state after {self.max_retries} retries.")

        state_data_file = self.key_file(key=key, extension=extension)
        state_metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        if not state_data_file.exists():
            raise ThreatPatrolsException(f"State file {state_data_file} not found.")

        if not state_metadata_file.exists():
            await self.jittery_sleep()
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        async with aiofiles.open(state_data_file, "r") as f:
            state_data_json = await f.read()

        try:
            async with aiofiles.open(state_metadata_file, "r") as f:
                state_metadata = json.loads(await f.read())
        except json.decoder.JSONDecodeError:
            await self.jittery_sleep()
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        if state_metadata.get("key", "") != key:
            raise ThreatPatrolsException(f"Failed to read state mismatch {key=} in metadata file.")

        if int(state_metadata.get("len", "0")) != len(state_data_json):
            await self.jittery_sleep()
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        if state_metadata.get("sha256", "") != hashlib.sha256(state_data_json.encode("utf8")).hexdigest():
            await self.jittery_sleep()
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        return json.loads(state_data_json)

    async def remove_state(self, key: str, extension: str = "data") -> Path:
        state_data_file = self.key_file(key=key, extension=extension, mkdir_missing=True)
        state_metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        state_writelock_file = await self.writelock_state(key=key)

        try:
            os.unlink(state_data_file)
        except FileNotFoundError:
            pass

        try:
            os.unlink(state_metadata_file)
        except FileNotFoundError:
            pass

        try:
            os.unlink(state_writelock_file)
        except FileNotFoundError:
            pass

        return state_data_file

    async def save_state(self, key: str, data: Any, extension="data") -> Path:
        state_data_file = self.key_file(key=key, extension=extension, mkdir_missing=True)
        state_metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        state_data = json.dumps(jsonable_encoder(data), separators=(",", ":"))
        metadata = {
            "key": key,
            "sha256": hashlib.sha256(state_data.encode("utf8")).hexdigest(),
            "len": len(state_data),
            "timestamp": str(datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0).isoformat()),
        }
        state_metadata = json.dumps(metadata, separators=(",", ":"))

        state_writelock_file = await self.writelock_state(key=key)

        async with aiofiles.open(state_data_file, "w") as fw1:
            await fw1.write(state_data)
        async with aiofiles.open(state_metadata_file, "w") as fw2:
            await fw2.write(state_metadata)

        try:
            os.unlink(state_writelock_file)
        except FileNotFoundError:
            pass

        return state_data_file

    async def writelock_state(self, key, _retry_count=0) -> Path:

        if _retry_count > self.max_retries:
            raise ThreatPatrolsException(f"Failed to create writelock after {self.max_retries} retries.")

        writelock_file = self.key_file(key=key, extension="writelock")
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
                    return await self.writelock_state(key=key, _retry_count=_retry_count + 1)
        except FileNotFoundError:
            await self.jittery_sleep()
            return await self.writelock_state(key=key, _retry_count=_retry_count + 1)

        return writelock_file

    async def jittery_sleep(self, sleep_seconds: Optional[float] = None, jitter_p: float = 0.75):
        if not sleep_seconds:
            sleep_seconds = self.sleep_wait_seconds
        sleep_milliseconds = int(sleep_seconds * 1000)
        jitter_half_milliseconds = int((sleep_seconds * jitter_p)/2 * 1000)
        sleep_ms = randrange(
            start=sleep_milliseconds - jitter_half_milliseconds, stop=sleep_milliseconds + jitter_half_milliseconds
        )
        # print(f"{sleep_ms=}")
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
