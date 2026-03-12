"""
Structured logging module for the NBA Prediction Agent System.

Provides consistent, structured logging across all agents and components
with contextual information (agent name, matchup, execution time).
"""
import logging
import sys
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any


LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """Initialize the logging system with structured format."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.handlers:
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "chromadb", "openai"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger for a specific component."""
    return logging.getLogger(f"nba.{name}")


@contextmanager
def log_execution_time(logger: logging.Logger, operation: str):
    """Context manager to log the execution time of an operation."""
    start = time.time()
    logger.info(f"[START] {operation}")
    try:
        yield
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"[FAILED] {operation} after {elapsed:.2f}s - {type(e).__name__}: {e}")
        raise
    else:
        elapsed = time.time() - start
        logger.info(f"[DONE] {operation} completed in {elapsed:.2f}s")


def log_agent(agent_name: str):
    """Decorator to add logging and timing to agent node functions."""
    def decorator(func):
        logger = get_logger(f"agent.{agent_name}")

        @wraps(func)
        def wrapper(state: dict) -> dict:
            home = state.get("team_home", "?")
            away = state.get("team_away", "?")
            with log_execution_time(logger, f"{agent_name} | {home} vs {away}"):
                result = func(state)
            return result

        @wraps(func)
        async def async_wrapper(state: dict) -> dict:
            home = state.get("team_home", "?")
            away = state.get("team_away", "?")
            with log_execution_time(logger, f"{agent_name} | {home} vs {away}"):
                result = await func(state)
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator
