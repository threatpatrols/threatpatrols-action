from typing import Callable

from pydantic import ValidationError

tpas_action_commands = ["call"]
tpas_non_action_commands = ["call-get", "call-list", "task-get", "task-list"]
tpas_commands = tpas_action_commands + tpas_non_action_commands


from .. import action_functions, action_models
from ..exceptions import ThreatPatrolsException
from ..shared.lib.logger_init import logger_get, logger_setlevel
from ..shared.models import HealthResponse, TaskItem, TaskState
from ..shared.validators.models import action_model_validator
from .lib.args import parse_action_args
from .lib.command_router import CommandRouter

action_models.Task = TaskItem
action_models.TaskState = TaskState
action_models.HealthResponse = HealthResponse


def load_cli_app(config, action: Callable):

    # Set the logger level early
    logger = logger_get(name=config.LOGGER_NAME)
    logger_setlevel(name=config.LOGGER_NAME, loglevel=config.LOGGER_LEVEL)

    try:
        return load_cli_app_wrapper(config, action)
    except (ValueError, ThreatPatrolsException, ValidationError) as e:
        logger.error(str(e))
        logger.debug("stack-trace", exc_info=e)
        exit(1)


def load_cli_app_wrapper(config, action: Callable):

    # Check action supplied models
    action_model_validator(action_models=action_models)

    # Assign the primary action_function
    setattr(action_functions, config.ACTION_NAME, action)

    # Get dynamic cli args based on the ActionRequest model fields
    action_args = parse_action_args(fields=action_models.ActionRequest.model_fields)

    return CommandRouter(args=action_args, action_name=config.ACTION_NAME)
