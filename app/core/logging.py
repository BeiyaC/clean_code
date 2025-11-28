import contextvars
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pythonjsonlogger import json as jsonlogger

ctx_correlation_id = contextvars.ContextVar("correlation_id", default="00000000-0000-4000-0000-000000000000")
ctx_step = contextvars.ContextVar("step", default=0)
custom_ctx: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "custom_logging_ctx", default=None
)

logger = logging.getLogger("default")


def _set_context(correlation_id: str, step: int, custom: Optional[Dict[str, Any]] = None):
    correlation_token = ctx_correlation_id.set(correlation_id or str(uuid4()))
    step_token = ctx_step.set(step)
    custom_token = custom_ctx.set(custom)
    return correlation_token, step_token, custom_token


def _reset_context(
    correlation_token: contextvars.Token, step_token: contextvars.Token, custom_token: contextvars.Token
):
    ctx_correlation_id.reset(correlation_token)
    ctx_step.reset(step_token)
    custom_ctx.reset(custom_token)


@contextmanager
def log_context(correlation_id: str, step: int, custom: Optional[Dict[str, Any]] = None):
    correlation_token, step_token, custom_token = _set_context(correlation_id, step, custom)
    yield
    _reset_context(correlation_token, step_token, custom_token)


class Formatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["correlation_id"] = ctx_correlation_id.get()
        log_record["step"] = ctx_step.get()
        log_record.update(custom_ctx.get() or {})


def initialize_logger(
    log_level: str = "INFO", logger_name: str = "default", formatter: Optional[Formatter] = None
) -> logging.Logger:
    _logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter or Formatter())
    _logger.addHandler(handler)
    _logger.setLevel(log_level)
    return _logger
