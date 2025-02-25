#
#  Copyright (c) 2025 Threat Patrols Pty Ltd <contact@threatpatrols.com>
#  See LICENSE.md for terms
#

import os
import sys
from pathlib import Path

from dynaconf import Dynaconf, Validator

from . import __initials__, __title__, __version__

ENVVAR_PREFIX = __initials__.upper()
TRUTHY_TERMS = ["true", "yes", "enable", "on"]

root_path = None
if not os.environ.get("ROOT_PATH_FOR_DYNACONF"):
    root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

os.environ["ENV_FOR_DYNACONF"] = "action"  # root dict.key in config.yml


class DynaconfSettings(Dynaconf):
    TITLE: str
    VERSION: str
    ACTION_NAME: str

    TPAS_VERSION: str

    STATE__TYPE: str
    STATE__PARAMS: dict
    STATE__CALLS__TTL_SECONDS: int
    STATE__TASKS__TTL_SECONDS: int

    USER_TAG_MAX_COUNT: int
    USER_TAG_MAX_KEY_LENGTH: int
    USER_TAG_MAX_VALUE_LENGTH: int

    SWAGGER_UI_JS_URL: str
    SWAGGER_UI_CSS_URL: str
    SWAGGER_UI_CSS_OVERRIDES_URL: str
    SWAGGER_UI_FAVICON_URL: str

    DEBUG: bool
    LOGGER_NAME: str
    LOGGER_LEVEL: str
    CONFIG_FILE: Path

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overrides()
        self.validators.validate()  # apply validation to updates and constants

    def overrides(self):
        self.TITLE = __title__
        self.VERSION = "dev"
        self.TPAS_VERSION = __version__

        self.USER_TAG_MAX_COUNT = 16
        self.USER_TAG_MAX_KEY_LENGTH = 64
        self.USER_TAG_MAX_VALUE_LENGTH = 256

        # https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.18.2/swagger-ui-bundle.min.js
        # https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.18.2/swagger-ui.min.css
        self.SWAGGER_UI_JS_URL = "/docs/static/js/swagger-ui-bundle-v5.18.2.min.js"
        self.SWAGGER_UI_CSS_URL = "/docs/static/css/swagger-ui-v5.18.2.min.css"
        self.SWAGGER_UI_CSS_OVERRIDES_URL = "/docs/static/css/overrides.css"

        self.LOGGER_NAME = __initials__.lower()
        self.LOGGER_LEVEL = self.__get_logger_level()
        self.DEBUG = True if self.LOGGER_LEVEL.lower() == "debug" else False

    def __get_logger_level(self):
        if "--quiet" in sys.argv or os.getenv(f"{ENVVAR_PREFIX}_QUIET", "").lower().strip() in TRUTHY_TERMS:
            return "fatal"
        elif "--debug" in sys.argv or os.getenv(f"{ENVVAR_PREFIX}_DEBUG", "").lower().strip() in TRUTHY_TERMS:
            return "debug"
        return "info"


setting_validators = [
    Validator("LOGGER_LEVEL", is_in=["debug", "info", "warning", "error", "critical"], default="info"),
    Validator("SWAGGER_UI_FAVICON_URL", is_type_of=str, default="https://www.threatpatrols.com/favicon.ico"),
    Validator("STATE__TYPE", is_type_of=str, default="filesystem"),
    Validator("STATE__PARAMS", is_type_of=dict, default={"root_path": "/tmp/tpas"}),
    Validator("STATE__CALLS__TTL_SECONDS", is_type_of=int, default=3600 * 2),
    Validator("STATE__TASKS__TTL_SECONDS", is_type_of=int, default=3600 * 2),
]


def find_config_in_subpaths(config_filepaths: list[Path]):
    subpaths = [Path("."), Path(os.getcwd()), Path(os.getcwd()) / ".."]
    for config_filepath in config_filepaths:
        if config_filepath.is_file():
            return config_filepath.resolve()
        for subpath in subpaths:
            config_subpath = subpath / Path(config_filepath)
            if config_subpath.is_file():
                return config_subpath.resolve()


envvar = os.getenv(f"{ENVVAR_PREFIX}_CONFIG_FILE", "")
if envvar:
    config_file = find_config_in_subpaths(config_filepaths=[Path(envvar)])
else:
    config_file = find_config_in_subpaths(config_filepaths=[Path("config.yml"), Path("config.yaml")])


config = DynaconfSettings(
    load_dotenv=False,
    envvar_prefix=ENVVAR_PREFIX,
    environments=True,
    settings_files=[config_file],
    root_path=root_path,
    validators=setting_validators,
)

config.CONFIG_FILE = config_file
