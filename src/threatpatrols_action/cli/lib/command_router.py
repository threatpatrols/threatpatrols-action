import asyncio
from logging import getLogger
from typing import Optional

from rich import print_json

from ... import config
from ...shared.controllers.calls import tpas_call, tpas_call_get, tpas_call_list
from ...shared.controllers.tasks import tpas_task_get, tpas_task_list
from ...shared.lib.casts import list_to_dict
from ...shared.lib.jsonable import jsonable_encoder
from .. import action_models, tpas_commands

logger = getLogger(config.LOGGER_NAME)


class CommandRouter:

    args: dict
    action_name: str
    tpas_command: str
    tpas_identifier: Optional[str] = None

    def __init__(self, args: dict, action_name: str):

        self.tpas_command = args.get("tpas_command")[0]
        if args.get("tpas_require_override") and len(args.get("tpas_command")) > 1:
            self.tpas_identifier = args.get("tpas_command")[1]

        if (not self.tpas_command) or (self.tpas_command not in tpas_commands):
            raise ValueError("Unsupported TPAS command requested.")

        if "tpas_tags" in args.keys():
            args["_tags"] = list_to_dict(args.get("tpas_tags"))

        self.args = args
        self.action_name = action_name

    def __call__(self):

        # command: call
        # ===
        if self.tpas_command == "call":
            args = {
                "action_name": self.action_name,
                "action_args": action_models.ActionRequest(**self.args).model_dump(),
            }
            asyncio.run(self._async_caller(tpas_call, args))

        # command: call-get
        # ===
        elif self.tpas_command == "call-get":
            args = {"call_id": self.tpas_identifier}
            asyncio.run(self._async_caller(tpas_call_get, args))

        # command: call-list
        # ===
        elif self.tpas_command == "call-list":
            args = {}
            asyncio.run(self._async_caller(tpas_call_list, args))

        # command: task-get
        # ===
        elif self.tpas_command == "task-get":
            args = {"task_id": self.tpas_identifier}
            asyncio.run(self._async_caller(tpas_task_get, args))

        # command: task-list
        # ===
        elif self.tpas_command == "task-list":
            args = {}
            asyncio.run(self._async_caller(tpas_task_list, args))

        else:
            raise ValueError("Unsupported TPAS command requested in __call__.")

    async def _async_caller(self, func, kwargs):
        result = await func(**kwargs)
        print_json(data=jsonable_encoder(result))
