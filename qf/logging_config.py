import logging
import os
import sys

import structlog
from structlog.types import EventDict
from structlog.types import Processor
from structlog.types import WrappedLogger

_SHARED_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.LINENO,
            structlog.processors.CallsiteParameter.FUNC_NAME,
        }
    ),
]


def _gcp_renamer(_logger: WrappedLogger, _method_name: str, event_dict: EventDict) -> EventDict:
    """Rename structlog keys to the fields GCP Cloud Logging expects."""
    if "level" in event_dict:
        event_dict["severity"] = str(event_dict.pop("level")).upper()
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    if "exception" in event_dict:
        event_dict["stack_trace"] = event_dict.pop("exception")
    return event_dict


def configure_logging(log_level: str, *, is_local_dev: bool | None = None) -> None:
    """Configure structlog + stdlib interop for the kill-test run.

    Local dev (a TTY) renders coloured console output; otherwise emits one JSON
    object per line with GCP-style `severity`/`message`/`timestamp` fields. Stdlib
    logs from dependencies are routed through the same formatter so the stream
    stays single-format.
    """
    if is_local_dev is None:
        is_local_dev = sys.stderr.isatty() and os.getenv("TERM") is not None

    if is_local_dev:
        enrichment: list[Processor] = [
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
        ]
        renderer: Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        enrichment = [
            structlog.processors.TimeStamper(
                key="timestamp", fmt="%Y-%m-%dT%H:%M:%S.%fZ", utc=True
            ),
            _gcp_renamer,
        ]
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            *enrichment,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=[*_SHARED_PROCESSORS, *enrichment],
            processor=renderer,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())
