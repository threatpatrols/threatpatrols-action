import asyncio
from typing import Callable

from .. import action_functions, action_models
from ..shared.lib.action_caller import foreground_action_caller
from ..shared.lib.logger_init import logger_get, logger_setlevel
from ..shared.models import HealthResponse, TaskItem, TaskState
from ..shared.validators.models import action_model_validator

action_models.Task = TaskItem
action_models.TaskState = TaskState
action_models.HealthResponse = HealthResponse


def load_cli_app(config, action: Callable):

    # Set the logger level early
    logger = logger_get(name=config.LOGGER_NAME)
    logger_setlevel(name=config.LOGGER_NAME, loglevel=config.LOGGER_LEVEL)

    logger.info(f"{config.TITLE} v{config.VERSION}")
    logger.info(f"CONFIG_FILE = {str(config.CONFIG_FILE)}")

    # Check action supplied models
    action_model_validator(action_models=action_models)

    # Assign the primary action_function
    setattr(action_functions, config.ACTION_NAME, action)

    return ThreatpatrolsActionCliAppWrapper(config)


class ThreatpatrolsActionCliAppWrapper:

    def __init__(self, config):
        self.config = config

    def run(self):

        request_data = action_models.ActionRequest(
            url="https://www.google.com",
            referer="https://www.google.com/",
            user_agent="",
            headers={},
            proxy="socks5://127.0.0.1:1080",
        ).model_dump()

        action_function = getattr(action_functions, self.config.ACTION_NAME)

        asyncio.run(self.__async(action_function, **request_data))


    async def __async(self, action_function, **action_args):

        action_response = await foreground_action_caller(action_function, **action_args)
        print(action_response)
