import logging
from typing import Optional


_LOGGER_CACHE: dict[str, logging.Logger] = {}


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]
    setup_logging(level or "INFO")
    logger = logging.getLogger(name)
    _LOGGER_CACHE[name] = logger
    return logger
