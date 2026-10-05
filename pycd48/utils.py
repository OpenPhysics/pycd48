"""
Shared utilities for CD48.

This module provides common utility functions used across
sync and async CD48 implementations.
"""

from __future__ import annotations

import logging

import serial.tools.list_ports

from .constants import (
    CYPRESS_PRODUCT_ID,
    CYPRESS_VENDOR_ID,
    DAC_MAX_BYTE,
    DAC_MAX_VOLTAGE,
    NUM_CHANNELS,
)

_logger = logging.getLogger(__name__)


# =============================================================================
# Base Exceptions (defined here to avoid circular imports)
# =============================================================================


class CD48Error(Exception):
    """Base exception for CD48 errors."""

    pass


class CD48DeviceNotFoundError(CD48Error):
    """Raised when CD48 device cannot be found."""

    pass


class CD48OverflowError(CD48Error):
    """Raised when a measured channel's overflow bit is set."""

    pass


def find_cd48_port(
    vendor_id: int = CYPRESS_VENDOR_ID,
    product_id: int = CYPRESS_PRODUCT_ID,
    logger: logging.Logger | None = None,
) -> str:
    """
    Attempt to auto-detect CD48 on serial ports.

    A port matches only when both the Cypress vendor id and product id match.
    Generic USB or serial adapters are not opened.

    Parameters:
    -----------
    vendor_id : int
        USB Vendor ID to look for (default: Cypress VENDOR_ID)
    product_id : int
        USB Product ID to look for (default: Cypress PRODUCT_ID)
    logger : logging.Logger, optional
        Logger instance for debug output

    Returns:
    --------
    str : The detected serial port device path

    Raises:
    -------
    CD48DeviceNotFoundError
        If no CD48 device can be found
    """
    log = logger or _logger
    ports = serial.tools.list_ports.comports()

    for port in ports:
        if port.vid == vendor_id and port.pid == product_id:
            log.info(f"Found CD48 (Cypress): {port.device} - {port.description}")
            return str(port.device)

    raise CD48DeviceNotFoundError("Could not find CD48. Please specify port manually.")


def validate_channel(channel: int) -> None:
    """
    Validate that a channel number is in the valid range.

    Parameters:
    -----------
    channel : int
        Channel number to validate

    Raises:
    -------
    ValueError
        If channel is not in range 0 to NUM_CHANNELS-1
    """
    if not 0 <= channel < NUM_CHANNELS:
        raise ValueError(f"Channel must be 0-{NUM_CHANNELS - 1}, got {channel}")


def validate_binary_input(name: str, value: int) -> None:
    """
    Validate that a value is a binary input (0 or 1).

    Parameters:
    -----------
    name : str
        Name of the parameter (for error message)
    value : int
        Value to validate

    Raises:
    -------
    ValueError
        If value is not 0 or 1
    """
    if value not in (0, 1):
        raise ValueError(f"{name} must be 0 or 1, got {value}")


def voltage_to_dac_byte(voltage: float) -> int:
    """
    Convert a voltage value to DAC byte value.

    Parameters:
    -----------
    voltage : float
        Voltage to convert (0.0 to DAC_MAX_VOLTAGE)

    Returns:
    --------
    int : DAC byte value (0 to 255), clamped to valid range
    """
    # Match Math.round for this positive range (half away from zero / half up).
    byte_val = int(round((voltage / DAC_MAX_VOLTAGE) * DAC_MAX_BYTE))
    return max(0, min(DAC_MAX_BYTE, byte_val))


def validate_duration(duration: float) -> None:
    """Raise ValueError when a measurement duration is not positive."""
    if duration <= 0:
        raise ValueError(f"duration must be greater than 0, got {duration}")


def command_clears_counters(command: str) -> bool:
    """Return True when the command reads and clears hardware counters."""
    return command[:1] in {"c", "C"}


def ensure_no_channel_overflow(overflow: int, *channels: int) -> None:
    """
    Raise when any listed channel's overflow bit is set.

    A set bit means the counter wrapped, so a rate computed from the raw
    count would be silently low.
    """
    overflowed = [channel for channel in channels if overflow & (1 << channel)]
    if overflowed:
        listed = ", ".join(str(channel) for channel in overflowed)
        raise CD48OverflowError(
            f"Counter overflow on channel(s) {listed}; "
            f"rate would be understated (overflow={overflow})"
        )


def dac_byte_to_voltage(byte_val: int) -> float:
    """
    Convert a DAC byte value to voltage.

    Parameters:
    -----------
    byte_val : int
        DAC byte value (0 to 255)

    Returns:
    --------
    float : Voltage value (0.0 to DAC_MAX_VOLTAGE)
    """
    return (byte_val / DAC_MAX_BYTE) * DAC_MAX_VOLTAGE
