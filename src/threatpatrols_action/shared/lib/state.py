import asyncio
import datetime
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles

from ...exceptions import ThreatPatrolsException
from .jsonable import jsonable_encoder

DEFAULT_STATE_TTL_SECONDS = 3600 * 8

DEFAULT_STATE_FILESYSTEM_ROOT_PATH = "/tmp/tpas"
DEFAULT_STATE_FILESYSTEM_MAX_WAIT_SECONDS = 30
DEFAULT_STATE_FILESYSTEM_SLEEP_WAIT_SECONDS = 0.5
DEFAULT_STATE_FILESYSTEM_MAX_RETRIES = 8


class StateHandlerFilesystem:

    root_path: Path
    state_ttl_seconds: int
    max_wait_seconds: int
    sleep_wait_seconds: float
    max_retries: int = 8

    def __init__(
        self,
        state_ttl_seconds: int,
        max_wait_seconds: int,
        sleep_wait_seconds: float,
        max_retries: int,
        root_path: Path,
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

    async def stale_state_reaper(self, key):
        pass

    async def load_state(self, key: str, extension: str = "data", _retry_count=0):

        if _retry_count > self.max_retries:
            raise ThreatPatrolsException(f"Failed to read state after {self.max_retries} retries.")

        state_data_file = self.key_file(key=key, extension=extension)
        state_metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        if not state_data_file.exists():
            raise ThreatPatrolsException(f"State file {state_data_file} not found.")

        if not state_metadata_file.exists():
            await asyncio.sleep(self.sleep_wait_seconds)
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        async with aiofiles.open(state_data_file, "r") as f:
            state_data_json = await f.read()

        try:
            async with aiofiles.open(state_metadata_file, "r") as f:
                state_metadata = json.loads(await f.read())
        except json.decoder.JSONDecodeError:
            await asyncio.sleep(self.sleep_wait_seconds)
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        if state_metadata.get("key", "") != key:
            raise ThreatPatrolsException(f"Failed to read state mismatch {key=} in metadata file.")

        if int(state_metadata.get("len", "0")) != len(state_data_json):
            await asyncio.sleep(self.sleep_wait_seconds)
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        if state_metadata.get("sha256", "") != hashlib.sha256(state_data_json.encode("utf8")).hexdigest():
            await asyncio.sleep(self.sleep_wait_seconds)
            return await self.load_state(key=key, _retry_count=_retry_count + 1)

        return json.loads(state_data_json)

    async def save_state(self, key: str, data: Any, extension="data") -> Path:
        state_data_file = self.key_file(key=key, extension=extension, mkdir_missing=True)
        state_metadata_file = self.key_file(key=key, extension=f"{extension}.metadata")

        state_data_json = json.dumps(jsonable_encoder(data))
        state_metadata_string = json.dumps(
            {
                "key": key,
                "sha256": hashlib.sha256(state_data_json.encode("utf8")).hexdigest(),
                "len": len(state_data_json),
                "timestamp": str(datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0).isoformat()),
            }
        )

        state_writelock_file = await self.writelock_state(key=key)

        async with aiofiles.open(state_data_file, "w") as fw1:
            await fw1.write(state_data_json)
        async with aiofiles.open(state_metadata_file, "w") as fw2:
            await fw2.write(state_metadata_string)

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
            await asyncio.sleep(self.sleep_wait_seconds)
            if time.time() > max_wait_until:
                raise ThreatPatrolsException(f"Failed to acquire writelock after {self.max_wait_seconds} seconds.")

        with open(writelock_file, "w") as fw:
            fw.write(writelock_content)
        async with aiofiles.open(writelock_file, "r") as fr:
            if await fr.read() != writelock_content:
                return await self.writelock_state(key=key, _retry_count=_retry_count + 1)

        return writelock_file


def get_state_handler(
    storage: str,
    state_ttl_seconds: int = DEFAULT_STATE_TTL_SECONDS,
    state_filesystem_max_wait_seconds: int = DEFAULT_STATE_FILESYSTEM_MAX_WAIT_SECONDS,
    state_filesystem_sleep_wait_seconds: float = DEFAULT_STATE_FILESYSTEM_SLEEP_WAIT_SECONDS,
    state_filesystem_max_retries: int = DEFAULT_STATE_FILESYSTEM_MAX_RETRIES,
    state_filesystem_root_path: str = DEFAULT_STATE_FILESYSTEM_ROOT_PATH,
) -> StateHandlerFilesystem:
    if storage == "filesystem":
        return StateHandlerFilesystem(
            state_ttl_seconds=state_ttl_seconds,
            max_wait_seconds=state_filesystem_max_wait_seconds,
            sleep_wait_seconds=state_filesystem_sleep_wait_seconds,
            max_retries=state_filesystem_max_retries,
            root_path=Path(state_filesystem_root_path),
        )

    raise ThreatPatrolsException("StateHandler only supports filesystem at this time.")
