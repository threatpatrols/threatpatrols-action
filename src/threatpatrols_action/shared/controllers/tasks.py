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

from fastapi import BackgroundTasks
from hlid import HLID

from ... import action_functions, config
from ...shared.lib.callers import background_action_caller
from ...shared.lib.casts import dict_to_flat_string
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskItem, TaskItemSummary, TaskState
from ...shared.validators.hlids import validate_hlid

logger = logging.getLogger(config.LOGGER_NAME)
state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
)


async def tpas_task(
    action_name: str, action_args: dict, task_id: str = None, background_tasks: BackgroundTasks = None
) -> TaskItem:

    if not task_id:
        task_id = str(HLID())
    else:
        validate_hlid(task_id, location_hint="tpas_task")

    action_args["_tags"]["task_id"] = task_id
    action_args["_tags"] = dict(sorted(action_args["_tags"].items()))

    logger.info("Background create: " + dict_to_flat_string(data=action_args["_tags"]))
    action_function = getattr(action_functions, action_name)
    background_tasks.add_task(background_action_caller, action_function=action_function, task_id=task_id, **action_args)

    return TaskItem(
        task_id=task_id, state=TaskState.PENDING, _tags=action_args["_tags"], _callbacks=action_args["_callbacks"]
    )


async def tpas_task_get(task_id: str) -> TaskItem:

    validate_hlid(task_id, location_hint="tpas_task_get")

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    task_data = await state_handler.load_state(key=state_key)

    return TaskItem(**task_data)


async def tpas_task_list(filter_expired_ttl: bool = False, purge_expired_ttl: bool = False) -> list[TaskItemSummary]:

    tasks = []
    if filter_expired_ttl or purge_expired_ttl:
        for item in await state_handler.find_states(key="tasks", filter_expired_ttl=True):
            tasks.append(TaskItemSummary(**item))
        if purge_expired_ttl:
            logger.warning(f"Purging {len(tasks)} expired_ttl tasks from state storage.")
            for task in tasks:
                state_key = "tasks/" + task.task_id.split("-")[0] + "/" + task.task_id
                await state_handler.remove_state(key=state_key)
            tasks = []
    else:
        for item in await state_handler.find_states(key="tasks", filter_expired_ttl=False):
            tasks.append(TaskItemSummary(**item))

    return tasks
