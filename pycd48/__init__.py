"""
pycd48 - Python interface for the CD48 Coincidence Counter

A simple library for controlling the Red Dog Physics CD48 Coincidence Counter
via USB serial interface.
"""

from .cd48 import CD48

__version__ = "0.1.0"
__all__ = ["CD48"]
