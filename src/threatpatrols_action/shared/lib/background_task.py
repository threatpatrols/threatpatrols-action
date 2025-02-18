import logging
from functools import wraps
from typing import Any, Callable

from ... import config

logger = logging.getLogger(config.LOGGER_NAME)


def background_task_observability(func: Callable) -> Callable:
    """
    Function decorator that provides observability for background tasks via logged-tasks and
    logged-exceptions
    Credit: https://johachi.hashnode.dev/important-gotchas-with-backgroundtasks-in-fastapi
    """
    task_name = func.__name__

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:

        #
        # NB: failures inside this function are >>SILENT<<  If something related to background tasks is not
        # working, then consider this function carefully.  Don't be in a rush to change the code in this function!
        #

        if not kwargs.get("_tags") or not kwargs.get("_tags").get("task_id"):
            logger.error("Background tasks MUST provide '_tags.task_id' value in kwargs.")
            return

        task_id = kwargs.get("_tags").get("task_id")
        logger.info(f"background_task [{task_id}] {task_name}() started.")

        try:
            await func(*args, **kwargs)
            logger.info(f"background_task [{task_id}] {task_name}() finished successfully")
        except Exception as e:
            log_message = f"background_task [{task_id}] {task_name}() failed permanently with error: {e.__repr__()!r}"
            if logger.level <= 10:  # 10 == logging.DEBUG
                logger.error(msg=log_message, exc_info=True)
            else:
                logger.error(msg=log_message)

    return wrapper
