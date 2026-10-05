from __future__ import annotations

import logging
from pathlib import Path

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_configured = False


def configure(level: int = logging.INFO) -> None:
    """Configure root logging once (console)."""
    global _configured
    if _configured:
        return
    logging.basicConfig(level=level, format=_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def add_file_handler(logger: logging.Logger, path: Path) -> logging.Handler:
    """Attach a file handler (used per stage). Caller must remove it afterwards."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(handler)
    return handler
