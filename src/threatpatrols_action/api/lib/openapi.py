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
            title=self.app.title,
            version=self.app.version,
            summary=self.app.summary,
            description='More awesome Threat Patrols Actions at <strong><a href="https://github.com/threatpatrols"'
            ' rel="noreferrer noopener">github.com/threatpatrols</a></strong>',
            routes=self.app.routes,
        )

        # Remove some unnecessary cruft from the regular openapi_schema
        for schema_path in openapi_schema["paths"]:
            for method in openapi_schema["paths"][schema_path]:
                openapi_schema["paths"][schema_path][method]["responses"].pop("400", None)  # Bad Request
                openapi_schema["paths"][schema_path][method]["responses"].pop("422", None)  # Unprocessable Entity

        return openapi_schema
