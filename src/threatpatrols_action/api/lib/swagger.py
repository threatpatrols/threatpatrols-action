from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from ... import config

SWAGGER_UI_PAGE_TITLE = config.TITLE
SWAGGER_UI_JS_URL = config.SWAGGER_UI_JS_URL
SWAGGER_UI_CSS_URL = config.SWAGGER_UI_CSS_URL
SWAGGER_UI_CSS_OVERRIDES_URL = config.SWAGGER_UI_CSS_OVERRIDES_URL
SWAGGER_UI_FAVICON_URL = config.SWAGGER_UI_FAVICON_URL


def get_swagger_docs_html(doc_expansion: str = "list") -> str:
    swagger_ui_html = get_swagger_ui_html(
        openapi_url=f"/openapi.json",
        title=SWAGGER_UI_PAGE_TITLE,
        swagger_js_url=SWAGGER_UI_JS_URL,
        swagger_css_url=SWAGGER_UI_CSS_URL,
        swagger_favicon_url=SWAGGER_UI_FAVICON_URL,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,  # prevent the model Schema table from rendering
            "displayOperationId": False,
            "displayRequestDuration": True,
            "tryItOutEnabled": True,
            "requestSnippets": True,
            "tagsSorter": None,
            "operationsSorter": "method",
            "filter": False,
        },
    )
    return swagger_ui_html.body.decode()


def get_swagger_docs_response(doc_expansion: str = "list") -> HTMLResponse:

    swagger_ui_html = get_swagger_docs_html(doc_expansion=doc_expansion)
    threatpatrols_custom_html = f'<link rel="stylesheet" href="{SWAGGER_UI_CSS_OVERRIDES_URL}">'

    # NB: the unusual stylesheet placement at the end-of-body
    return HTMLResponse(swagger_ui_html.replace("</body>", f"{threatpatrols_custom_html}\n</body>"))
