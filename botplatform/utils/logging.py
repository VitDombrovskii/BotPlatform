from __future__ import annotations

import logging
from typing import Optional


def configure_logging(logger_name: str = "botplatform", level: int = logging.INFO) -> logging.Logger:
    """
    Базовая настройка логирования для BotPlatform.

    На старте:
    - пишет в stdout,
    - форматирует время, уровень, имя логгера и сообщение.
    """
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger  # уже настроен

    logger.setLevel(level)
    handler = logging.StreamHandler()
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
