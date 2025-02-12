import os.path
from typing import Callable

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from .. import action_models
from ..exceptions import generate_api_exception_response_handlers
from ..shared.lib.logger_init import logger_get, logger_setlevel
from .lib.openapi import custom_openapi
from .lib.validators import action_model_validator
from .middlewares import load_middlewares
from .models import HealthResponse, TaskResponse, TaskState
from .routes import ActionRoutes  # noqa: F401

action_models.TaskResponse = TaskResponse
action_models.TaskState = TaskState
action_models.HealthResponse = HealthResponse


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
    logger_get(name=config.LOGGER_NAME)
    logger_setlevel(name=config.LOGGER_NAME, loglevel=config.LOGGER_LEVEL)

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

    # Load action routes
    action_routes = ActionRoutes(action=action)

    # Include routes into the app itself
    app.include_router(action_routes.router)

    # Load app middleware
    load_middlewares(app=app)

    # Apply redirects
    add_static_route(app, request_path=f"/docs/static", files_directory="api/static")
    add_redirect_route(app, request_path="/", redirect_url="/docs", tags=["System"], summary="Redirect to docs.")

    # Customize the OpenAPI schema
    app.openapi_schema = custom_openapi(app)

    return app
