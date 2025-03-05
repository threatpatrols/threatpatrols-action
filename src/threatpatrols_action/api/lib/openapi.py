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

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from ... import config

ACTION_NAME = config.ACTION_NAME


def custom_openapi(app):
    return CustomOpenApiSchema(app)()


class CustomOpenApiSchema:

    app: FastAPI

    def __init__(self, app: FastAPI):
        self.app = app

    def __call__(self):
        if self.app.openapi_schema:
            return self.app.openapi_schema

        openapi_schema = get_openapi(
            title=config.TITLE,
            version=f"v{config.VERSION} | TPAS:v{config.TPAS_VERSION}",
            summary=self.app.summary,
            description="Discover more awesome Threat Patrols Actions at <strong> "
            '<a href="https://github.com/threatpatrols" rel="noreferrer noopener">github.com/threatpatrols</a>'
            "</strong>",
            routes=self.app.routes,
        )

        # Remove some unnecessary cruft from the regular openapi_schema
        for schema_path in openapi_schema["paths"]:
            for method in openapi_schema["paths"][schema_path]:
                openapi_schema["paths"][schema_path][method]["responses"].pop("400", None)  # Bad Request
                openapi_schema["paths"][schema_path][method]["responses"].pop("422", None)  # Unprocessable Entity

        return openapi_schema
