import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir

from ... import config
from ...exceptions import ThreatPatrolsException

logger = logging.getLogger(config.LOGGER_NAME)


@dataclass
class ExecuteCommand:

    command: str | None = None
    args: list | None = None
    env: dict | None = None
    runas: str | None = None
    cwd: str | None = None


@dataclass
class ExecuteCommandReturn:

    stdout: str | bytes | None = None
    stderr: str | bytes | None = None
    returncode: int | None = None


def execute_command(task: ExecuteCommand) -> ExecuteCommandReturn:

    logger.info(
        f"{task.command=} "
        f"args=<len:{len(task.args) if task.args else '0'}> "
        f"env=<len:{len(task.env) if task.env else '0'}>, "
        f"{task.runas=}, {task.cwd=}"
    )
    logger.debug(f"{task.command=} {task.args=}> {task.env=}> {task.runas=}, {task.cwd=}")

    if not task.cwd and task.runas and (Path("/home") / task.runas).exists():
        task.cwd = f"/home/{task.runas}"

    if not task.cwd:
        task.cwd = gettempdir()

    if task.args:
        task.args = [task.command] + task.args
    else:
        task.args = [task.command]

    if task.runas:
        task.args = ["sudo", "-u", task.runas] + task.args

    try:
        proc = subprocess.run(
            task.args,
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=task.cwd,
            env=task.env,
        )
    except Exception as e:
        raise ThreatPatrolsException(e)

    return ExecuteCommandReturn(stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
