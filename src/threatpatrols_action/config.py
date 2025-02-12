#
#  Copyright (c) 2025 Threat Patrols Pty Ltd <contact@threatpatrols.com>
#  See LICENSE.md for terms
#

import os
import sys
from pathlib import Path

from dynaconf import Dynaconf, Validator

from . import __initials__, __title__, __version__

ENVVAR_PREFIX = __initials__
TRUTHY_WORDS = ["true", "yes", "enable", "on"]

root_path = None
if not os.environ.get("ROOT_PATH_FOR_DYNACONF"):
    root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))


class DynaconfSettings(Dynaconf):
    TITLE: str
    VERSION: str
    ACTION_NAME: str

    API_PORT: int = 11235

    USER_TAG_MAX_COUNT: int = 16
    USER_TAG_MAX_KEY_LENGTH: int = 64
    USER_TAG_MAX_VALUE_LENGTH: int = 256

    # https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.18.2/swagger-ui-bundle.min.js
    # https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.18.2/swagger-ui.min.css

    SWAGGER_UI_JS_URL: str = "/docs/static/js/swagger-ui-bundle-v5.18.2.min.js"
    SWAGGER_UI_CSS_URL: str = "/docs/static/css/swagger-ui-v5.18.2.min.css"
    SWAGGER_UI_CSS_OVERRIDES_URL: str = "/docs/static/css/overrides.css"
    SWAGGER_UI_FAVICON_URL: str = "https://www.threatpatrols.com/favicon.ico"

    STATE_FILESYSTEM_ROOT_PATH: str = "/tmp/tpas"

    DEBUG: bool
    LOGGER_NAME: str
    LOGGER_LEVEL: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updates()
        self.validators.validate()  # apply validation to updates and constants

    def updates(self):
        self.TITLE = __title__
        self.VERSION = __version__
        self.LOGGER_NAME = __initials__.lower()
        self.LOGGER_LEVEL = self.__get_logger_level()
        self.DEBUG = True if self.LOGGER_LEVEL.lower() == "debug" else False

    def __get_logger_level(self):
        if "--quiet" in sys.argv or os.getenv(f"{ENVVAR_PREFIX}_QUIET", "").lower().strip() in TRUTHY_WORDS:
            return "fatal"
        elif "--debug" in sys.argv or os.getenv(f"{ENVVAR_PREFIX}_DEBUG", "").lower().strip() in TRUTHY_WORDS:
            return "debug"
        return "info"


setting_validators = [
    Validator("LOGGER_LEVEL", is_in=["debug", "info", "warning", "error", "critical"], default="info"),
]

settings_files = []
if os.getenv(f"{ENVVAR_PREFIX}_CONFIG_FILE"):
    settings_files.append(Path(os.getenv(f"{ENVVAR_PREFIX}_CONFIG_FILE")))
    settings_files.append(Path(os.getcwd()) / os.getenv(f"{ENVVAR_PREFIX}_CONFIG_FILE"))
    settings_files.append(Path(os.getcwd()) / ".." / os.getenv(f"{ENVVAR_PREFIX}_CONFIG_FILE"))
else:
    settings_files.append(Path("config.yml"))
    settings_files.append(Path("config.yaml"))
    settings_files.append(Path(os.getcwd()) / "config.yml")
    settings_files.append(Path(os.getcwd()) / "config.yaml")
    settings_files.append(Path(os.getcwd()) / ".." / "config.yml")
    settings_files.append(Path(os.getcwd()) / ".." / "config.yaml")

config = DynaconfSettings(
    load_dotenv=False,
    envvar_prefix=ENVVAR_PREFIX,
    environments=True,
    settings_files=settings_files,
    root_path=root_path,
    validators=setting_validators,
)
