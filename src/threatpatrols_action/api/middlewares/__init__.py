from .asgi_correlation_id import add_asgi_correlation_middleware
from .cors import add_cors_middleware
from .request_logger import add_request_logger_middleware


def load_middlewares(app):
    add_request_logger_middleware(app)
    add_asgi_correlation_middleware(app)
    add_cors_middleware(app)
