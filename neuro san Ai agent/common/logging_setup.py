"""Structured logging with secret redaction."""

from __future__ import annotations

import logging

from .redaction import redact_text


class _RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_text(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: (redact_text(str(v)) if isinstance(v, str) else v)
                                   for k, v in record.args.items()}
                elif isinstance(record.args, tuple):
                    record.args = tuple(redact_text(str(a)) if isinstance(a, str) else a
                                        for a in record.args)
        except Exception:
            pass
        return True


_configured = False
_orig_factory = logging.getLogRecordFactory()


def _redact_record_args(record: logging.LogRecord) -> None:
    try:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: (redact_text(str(v)) if isinstance(v, str) else v)
                               for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_text(str(a)) if isinstance(a, str) else a
                                    for a in record.args)
    except Exception:
        pass


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger once. Safe to call repeatedly."""
    global _configured
    if _configured:
        return
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # Logger-attached filters do NOT run for propagated child records,
    # so redact at record-creation time (covers caplog + all handlers).
    def _factory(*args: object, **kwargs: object) -> logging.LogRecord:
        record = _orig_factory(*args, **kwargs)
        _redact_record_args(record)
        return record

    logging.setLogRecordFactory(_factory)
    logging.getLogger().addFilter(_RedactingFilter())
    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
