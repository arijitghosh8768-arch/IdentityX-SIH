"""Structured logging configuration for the IdentityX backend."""

import logging
import sys
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """A colourful formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname:<8}{self.RESET}"
        return super().format(record)


def setup_logging(debug: bool = False):
    """Configure root and application loggers."""

    level = logging.DEBUG if debug else logging.INFO

    # Console handler with colours
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        ColoredFormatter(
            fmt="%(asctime)s │ %(levelname)s │ %(name)-28s │ %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Silence noisy third-party loggers
    for noisy in ("PIL", "easyocr", "matplotlib", "tensorflow", "urllib3", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("identityx").setLevel(level)
    logging.getLogger("identityx").info("Logging initialised (level=%s)", logging.getLevelName(level))


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger for the given module."""
    return logging.getLogger(f"identityx.{name}")
