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
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from hlid import HLID

from ... import action_models, config
from ...shared.controllers.tasks import tpas_task, tpas_task_get, tpas_task_list
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskItem, TaskItemSummary
from ...shared.validators.tags import validate_reserved_action_tags
from ..lib.headers import get_request_id_header, get_validated_api_key

ACTION_NAME = config.ACTION_NAME

router = APIRouter()
logger = logging.getLogger(config.LOGGER_NAME)
state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__TASKS__TTL_SECONDS,
)


@router.get(
    f"/{ACTION_NAME}/tasks",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Get a list of {ACTION_NAME!r} background task summary records.",
)
async def action_tasks_get_list(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
) -> list[TaskItemSummary]:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    return await tpas_task_list()


@router.get(
    f"/{ACTION_NAME}/tasks/{{task_id}}",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Get a full {ACTION_NAME} background task record by task_id.",
)
async def action_tasks_get_item(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    task_id: str,
) -> TaskItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    return await tpas_task_get(task_id)


@router.post(
    f"/{ACTION_NAME}/tasks",
    tags=[ACTION_NAME.replace("-", " ").replace("_", " ").title() + " background task action calls"],
    summary=f"Create a {ACTION_NAME!r} background task record and enqueue the action to be executed.",
)
async def action_tasks_post(
    api_key: Annotated[get_validated_api_key, Depends()],
    request_id: Annotated[get_request_id_header, Depends()],
    action_request: action_models.ActionRequest,
    background_tasks: BackgroundTasks,
) -> TaskItem:
    assert api_key is not None and len(api_key) > 0
    assert request_id is not None and len(request_id) > 0

    action_args = action_request.model_dump()

    # check for tag shenanigans
    validate_reserved_action_tags(tags=action_args.get("_tags"))

    # add some request specific tags
    task_id = str(HLID())
    action_args["_tags"]["request_id"] = request_id
    action_args["_tags"]["api_key_id"] = api_key.get("id")

    return await tpas_task(
        action_name=ACTION_NAME, action_args=action_args, task_id=task_id, background_tasks=background_tasks
    )
