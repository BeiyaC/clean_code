import logging
from typing import Any, Callable

from ariadne.asgi import GraphQL
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

load_dotenv(dotenv_path=".env", override=True)

from fastapi import FastAPI, Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core import ms_config
from app.core.context import get_context_value
from app.core.logging import ctx_correlation_id, ctx_step, log_context, logger
from app.graphql.http_handler import HTTPHandler
from app.graphql.schema import schema
from app.views.health_check import router as health_check_router


class GraphQLRedirect:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("path") in ("/graphql", "/v2/graphql", "/v2/graphql/"):
            scope["path"] = "/graphql/"
            scope["raw_path"] = b"/graphql/"
        await self.app(scope, receive, send)


class LogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record_args = record.args
        if isinstance(record_args, tuple):
            return len(record_args) >= 3 and record_args[2] not in ["/health_check", "/graphql/"]
        return False


logging.getLogger("uvicorn.access").addFilter(LogFilter())
app = FastAPI(title="app-core")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GraphQLRedirect)
app.mount(
    "/graphql",
    GraphQL(
        schema,
        context_value=get_context_value,
        debug=ms_config.is_dev_environment(),
        logger=logger,
        http_handler=HTTPHandler(),
    ),
)
app.include_router(health_check_router, prefix="/health_check")

@app.middleware("http")
async def add_http_header_for_logging(request: Request, call_next: Callable[..., Any]):
    correlation_id = request.headers.get("correlation_id") or "00000000-0000-4000-0000-000000000000"
    step = int(request.headers.get("step") or 0)
    with log_context(correlation_id, step):
        response = await call_next(request)
        response.headers.append("correlation_id", ctx_correlation_id.get())
        response.headers.append("step", str(ctx_step.get()))
        return response