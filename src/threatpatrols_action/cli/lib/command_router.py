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

import asyncio
from logging import getLogger
from typing import Optional

from pydantic import ValidationError
from rich import print_json

from ... import config
from ...exceptions import ThreatPatrolsException
from ...shared.controllers import tpas_call, tpas_call_get, tpas_call_list, tpas_task_get, tpas_task_list
from ...shared.lib.casts import list_to_dict
from ...shared.lib.jsonable import jsonable_encoder
from .. import action_models, tpas_commands

logger = getLogger(config.LOGGER_NAME)


class CommandRouter:

    args: dict
    action_name: str
    tpas_command: str
    tpas_identifier: Optional[str] = None
    tpas_list_modifier: Optional[str] = None

    def __init__(self, args: dict, action_name: str):

        if not args.get("tpas_command") or not isinstance(args.get("tpas_command"), list):
            raise ValueError("Invalid TPAS command.")

        self.tpas_command = args.get("tpas_command")[0]

        # *-get
        if self.tpas_command.endswith("-get") and len(args.get("tpas_command")) > 1:
            self.tpas_identifier = args.get("tpas_command")[1]

        # *-list
        elif self.tpas_command.endswith("-list") and len(args.get("tpas_command")) > 1:
            self.tpas_list_modifier = str(args.get("tpas_command", ["_", "_"])[1]).lower()
            if self.tpas_list_modifier not in ["expired", "expired-purge"]:
                raise ValueError("Unsupported list command modifier, use 'expired' or 'expired-purge'.")

        if self.tpas_command not in tpas_commands:
            raise ValueError("Unknown TPAS command.")

        if "tpas_tags" in args.keys():
            args["_tags"] = list_to_dict(args.get("tpas_tags"))

        if "tpas_callbacks" in args.keys():
            args["_callbacks"] = args.get("tpas_callbacks")

        self.args = args
        self.action_name = action_name

    def __call__(self):
        try:
            self.call_wrapper()
        except (ValueError, ThreatPatrolsException, ValidationError) as e:
            logger.fatal(str(e))
            logger.debug("stack-trace", exc_info=e)
            exit(1)

    def call_wrapper(self):

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
            args = self._handle_list_args()
            asyncio.run(self._async_caller(tpas_call_list, args))

        # command: task-get
        # ===
        elif self.tpas_command == "task-get":
            args = {"task_id": self.tpas_identifier}
            asyncio.run(self._async_caller(tpas_task_get, args))

        # command: task-list
        # ===
        elif self.tpas_command == "task-list":
            args = self._handle_list_args()
            asyncio.run(self._async_caller(tpas_task_list, args))

        else:
            raise ValueError("Unsupported TPAS command requested.")

    def _handle_list_args(self):
        args = {}
        if not self.tpas_list_modifier:
            return args
        if self.tpas_list_modifier.startswith("expired"):
            args["filter_expired_ttl"] = True
        if self.tpas_list_modifier.endswith("-purge"):
            args["purge_expired_ttl"] = True
        return args

    async def _async_caller(self, func, kwargs):
        result = await func(**kwargs)
        print_json(data=jsonable_encoder(result))
