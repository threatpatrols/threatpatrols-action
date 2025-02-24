import logging

from ... import config
from ...shared.lib.state import get_state_handler
from ...shared.models import TaskItem, TaskListItem
from ...shared.validators.hlids import validate_hlid

logger = logging.getLogger(config.LOGGER_NAME)
state_handler = get_state_handler(
    method=config.STATE__METHOD,
    method_params=config.STATE__PARAMS,
    state_ttl_seconds=config.STATE__CALLS__TTL_SECONDS,
)


async def tpas_task_get(task_id: str) -> TaskItem:

    validate_hlid(task_id, location_hint="tpas_task_get")

    state_key = "tasks/" + task_id.split("-")[0] + "/" + task_id
    task_data = await state_handler.load_state(key=state_key)

    return TaskItem(**task_data)


async def tpas_task_list(filter_expired_ttl: bool = False, purge_expired_ttl: bool = False) -> list[TaskListItem]:

    tasks = []
    if filter_expired_ttl or purge_expired_ttl:
        for item in await state_handler.find_states(key="tasks", filter_expired_ttl=True):
            tasks.append(TaskListItem(**item))
        if purge_expired_ttl:
            logger.warning(f"Purging {len(tasks)} expired_ttl tasks from state storage.")
            for task in tasks:
                state_key = "tasks/" + task.task_id.split("-")[0] + "/" + task.task_id
                await state_handler.remove_state(key=state_key)
            tasks = []
    else:
        for item in await state_handler.find_states(key="tasks", filter_expired_ttl=False):
            tasks.append(TaskListItem(**item))

    return tasks
