"""
pycd48 - Python interface for the CD48 Coincidence Counter

A simple library for controlling the Red Dog Physics CD48 Coincidence Counter
via USB serial interface.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .cd48 import (
    CD48,
    CD48DeviceNotFoundError,
    CD48Error,
    CD48ParseError,
    CoincidenceResult,
    CountsDict,
    RateResult,
)
from .logging import DataLogger, log_continuous

try:
    __version__ = version("pycd48")
except PackageNotFoundError:
    __version__ = "0.1.0"  # Fallback for development

__all__ = [
    "CD48",
    "CD48Error",
    "CD48ParseError",
    "CD48DeviceNotFoundError",
    "CountsDict",
    "RateResult",
    "CoincidenceResult",
    "DataLogger",
    "log_continuous",
    "__version__",
]
