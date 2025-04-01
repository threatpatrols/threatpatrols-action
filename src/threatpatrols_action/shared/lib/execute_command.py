#
# Copyright [2025] Threat Patrols Pty Ltd (https://www.threatpatrols.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir

from ... import config
from ...exceptions import ThreatPatrolsException

DEFAULT_EXEC_TIMEOUT_SECONDS = 30.0

logger = logging.getLogger(config.LOGGER_NAME)


@dataclass
class ExecuteCommand:
    command: str | None = None
    args: list | None = None
    env: dict | None = None
    runas: str | None = None
    cwd: str | None = None
    timeout: float = DEFAULT_EXEC_TIMEOUT_SECONDS


@dataclass
class ExecuteCommandReturn:
    stdout: str | bytes | None = None
    stderr: str | bytes | None = None
    returncode: int | None = None


def execute_command(command: ExecuteCommand) -> ExecuteCommandReturn:
    logger.info(
        f"{command.command=} "
        f"args=<len:{len(command.args) if command.args else '0'}> "
        f"env=<len:{len(command.env) if command.env else '0'}>, "
        f"{command.runas=}, {command.cwd=}"
    )
    logger.debug(f"{command.command=} {command.args=} {command.env=} {command.runas=} {command.cwd=}")

    if not command.cwd and command.runas and (Path("/home") / command.runas).is_dir():
        command.cwd = f"/home/{command.runas}"

    if not command.cwd:
        command.cwd = gettempdir()

    if command.args:
        command.args = [command.command] + command.args
    else:
        command.args = [command.command]

    if command.runas:
        command.args = ["sudo", "-u", command.runas] + command.args

    try:
        proc = subprocess.run(
            command.args,
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=command.cwd,
            env=command.env,
            timeout=command.timeout,
        )
    except Exception as e:
        raise ThreatPatrolsException(e)

    return ExecuteCommandReturn(stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
