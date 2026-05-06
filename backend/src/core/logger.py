"""
Logger - Singleton Pattern
Centralized logging with structured output
"""
import logging
import sys
from datetime import datetime
from typing import Optional


class Logger:
    _instance: Optional["Logger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> "Logger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self):
        self._logger = logging.getLogger("expense_tracker")
        self._logger.setLevel(logging.DEBUG)

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        if not self._logger.handlers:
            self._logger.addHandler(handler)

    def info(self, msg: str, **kwargs):
        self._logger.info(self._format(msg, **kwargs))

    def error(self, msg: str, **kwargs):
        self._logger.error(self._format(msg, **kwargs))

    def warning(self, msg: str, **kwargs):
        self._logger.warning(self._format(msg, **kwargs))

    def debug(self, msg: str, **kwargs):
        self._logger.debug(self._format(msg, **kwargs))

    def _format(self, msg: str, **kwargs) -> str:
        if kwargs:
            extras = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{msg} | {extras}"
        return msg


# Global singleton
logger = Logger()
