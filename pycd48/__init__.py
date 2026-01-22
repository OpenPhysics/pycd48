"""
pycd48 - Python interface for the CD48 Coincidence Counter

A simple library for controlling the Red Dog Physics CD48 Coincidence Counter
via USB serial interface.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .cd48 import (
    CD48,
    CD48ConfigError,
    CD48ConnectionError,
    CD48DeviceNotFoundError,
    CD48Error,
    CD48ParseError,
    CD48ResponseError,
    CD48WithReconnect,
    CoincidenceResult,
    CountsDict,
    DisconnectCallback,
    RateResult,
    ReconnectCallback,
)
from .experiments import ExperimentRunner, run_experiment
from .logging import DataLogger, log_continuous

try:
    __version__ = version("pycd48")
except PackageNotFoundError:
    __version__ = "0.1.0"  # Fallback for development


def _get_async_classes() -> tuple[type, type]:
    """Lazy import of async classes to avoid aioserial dependency at import time."""
    from .async_cd48 import AsyncCD48, AsyncCD48WithReconnect

    return AsyncCD48, AsyncCD48WithReconnect


__all__ = [
    # Core class
    "CD48",
    "CD48WithReconnect",
    # Exceptions
    "CD48Error",
    "CD48ParseError",
    "CD48DeviceNotFoundError",
    "CD48ConnectionError",
    "CD48ConfigError",
    "CD48ResponseError",
    # Type definitions
    "CountsDict",
    "RateResult",
    "CoincidenceResult",
    "DisconnectCallback",
    "ReconnectCallback",
    # Logging utilities
    "DataLogger",
    "log_continuous",
    # Experiment utilities
    "ExperimentRunner",
    "run_experiment",
    # Version
    "__version__",
]


def __getattr__(name: str) -> type:
    """Lazy loading for async classes to avoid aioserial import at module load."""
    if name == "AsyncCD48":
        from .async_cd48 import AsyncCD48

        return AsyncCD48
    elif name == "AsyncCD48WithReconnect":
        from .async_cd48 import AsyncCD48WithReconnect

        return AsyncCD48WithReconnect
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
