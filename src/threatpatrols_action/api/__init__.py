import os.path
from typing import Callable

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from .. import action_functions, action_models
from ..exceptions import ThreatPatrolsException, generate_api_exception_response_handlers
from ..shared.lib.logger_init import logger_get, logger_setlevel
from ..shared.models import HealthResponse, TaskItem, TaskState
from ..shared.validators.callbacks import callbacks_validator
from ..shared.validators.models import action_model_validator
from .lib.openapi import custom_openapi
from .lib.swagger import get_swagger_docs_response
from .middlewares import load_middlewares

action_models.Task = TaskItem
action_models.TaskState = TaskState
action_models.HealthResponse = HealthResponse

EXAMPLE_CREDENTIAL_KEY = "credential01example"  # prevent production usage with example credential key value.


def add_static_route(app: FastAPI, request_path: str, files_directory: str):
    if not files_directory.startswith("/"):
        files_directory = os.path.realpath("/".join(__file__.split("/")[:-2]) + "/" + files_directory)
    mount_name = request_path.replace("/", "_").replace(".", "_").replace("-", "_")
    app.mount(request_path, StaticFiles(directory=files_directory), name=mount_name)


def add_redirect_route(app: FastAPI, request_path, redirect_url, tags=None, summary=None, include_in_schema=False):
    @app.get(request_path, tags=tags, summary=summary, include_in_schema=include_in_schema)
    async def redirect_response():
        return RedirectResponse(url=redirect_url)


def load_api_app(config, action: Callable):

    # Set the logger level early
    logger = logger_get(name=config.LOGGER_NAME)
    logger_setlevel(name=config.LOGGER_NAME, loglevel=config.LOGGER_LEVEL)

    try:
        return load_api_app_wrapper(config, action, logger)
    except (ValueError, ThreatPatrolsException) as e:
        logger.fatal(str(e))
        logger.debug("stack-trace", exc_info=e)
        exit(1)


def load_api_app_wrapper(config, action: Callable, logger):

    logger.info(f"{config.TITLE}: v{config.VERSION} | Threat Patrols Actions: v{config.TPAS_VERSION}")
    logger.info(f"config_file={os.path.relpath(config.CONFIG_FILE)}")
    logger.debug("debug=true")

    # Prevent the default api key being available when not in debug mode
    if config.credentials.get(EXAMPLE_CREDENTIAL_KEY) and config.DEBUG is False:
        raise ThreatPatrolsException(f"Attempting to start API with {EXAMPLE_CREDENTIAL_KEY!r} in non debug-mode.")
    elif config.credentials.get(EXAMPLE_CREDENTIAL_KEY):
        logger.warning(f"Default {EXAMPLE_CREDENTIAL_KEY!r} enabled.")

    # Assign the primary action_function
    setattr(action_functions, config.ACTION_NAME, action)

    # Establish the FastAPI app instance
    app = FastAPI(
        debug=config.DEBUG,
        version=config.VERSION,
        title=config.TITLE,
        docs_url=None,
        exception_handlers=generate_api_exception_response_handlers(),
    )

    # Check action supplied models
    action_model_validator(action_models=action_models)

    # Check the callbacks are valid
    callbacks_validator(callbacks=config.callbacks)

    # Load routes
    from threatpatrols_action.api.routes import calls_routes, systems_routes, tasks_routes

    app.include_router(systems_routes)
    app.include_router(calls_routes)
    app.include_router(tasks_routes)

    # Load app middleware
    load_middlewares(app=app)

    if config.DEBUG:
        add_static_route(app, request_path="/docs/static", files_directory="api/static")
        add_redirect_route(app, request_path="/", redirect_url="/docs", tags=["System"], summary="Redirect to docs.")
        app.add_api_route("/docs", get_swagger_docs_response, methods=["GET"], tags=["System"], include_in_schema=False)

    # Customize the OpenAPI schema
    app.openapi_schema = custom_openapi(app)

    return app
