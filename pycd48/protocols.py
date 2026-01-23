"""
Protocol definitions for CD48 interface.

This module defines the common interface contract that both sync and async
CD48 implementations follow, enabling better type safety and interoperability.
"""

from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable


class CountsDict(TypedDict):
    """Type definition for parsed counts data."""

    counts: list[int]
    overflow: int


class RateResult(TypedDict):
    """Type definition for rate measurement results."""

    counts: int
    duration: float
    rate: float
    channel: int


class CoincidenceResult(TypedDict):
    """Type definition for coincidence measurement results."""

    singles_a: int
    singles_b: int
    coincidences: int
    duration: float
    rate_a: float
    rate_b: float
    coincidence_rate: float
    accidental_rate: float
    true_coincidence_rate: float


@runtime_checkable
class CD48Interface(Protocol):
    """
    Protocol defining the common interface for CD48 implementations.

    Both CD48 (sync) and AsyncCD48 implement this interface, allowing code
    to be written that works with either implementation via duck typing.

    Note: This protocol defines the synchronous method signatures. AsyncCD48
    implements async versions of these methods with the same names and signatures,
    but returning coroutines instead of direct values.
    """

    @property
    def is_connected(self) -> bool:
        """Return True if connected to the device."""
        ...

    @property
    def port(self) -> str | None:
        """Return the serial port name."""
        ...

    def close(self) -> None:
        """Close serial connection."""
        ...


@runtime_checkable
class CD48DeviceInterface(Protocol):
    """
    Extended protocol for CD48 device operations.

    This protocol defines the complete device control interface
    for type checking purposes.
    """

    @property
    def is_connected(self) -> bool:
        """Return True if connected to the device."""
        ...

    @property
    def port(self) -> str | None:
        """Return the serial port name."""
        ...

    def close(self) -> None:
        """Close serial connection."""
        ...

    def get_counts(self, human_readable: bool = True) -> str | CountsDict:
        """Get current counts from all channels."""
        ...

    def clear_counts(self) -> None:
        """Clear all counters."""
        ...

    def set_channel(self, channel: int, A: int = 0, B: int = 0, C: int = 0, D: int = 0) -> str:
        """Configure which inputs a counter watches."""
        ...

    def set_trigger_level(self, voltage: float) -> str:
        """Set trigger level voltage."""
        ...

    def set_impedance_50ohm(self) -> str:
        """Set input impedance to 50 Ohms."""
        ...

    def set_impedance_highz(self) -> str:
        """Set input impedance to high-Z."""
        ...

    def set_repeat(self, interval_ms: int) -> str:
        """Set automatic count reporting interval."""
        ...

    def toggle_repeat(self) -> str:
        """Toggle automatic repeat reporting on/off."""
        ...

    def get_settings(self, human_readable: bool = True) -> str:
        """Get all current settings."""
        ...

    def get_overflow(self) -> int:
        """Check and clear overflow status."""
        ...

    def set_dac_voltage(self, voltage: float) -> str:
        """Set DAC output voltage."""
        ...

    def get_version(self) -> str:
        """Get firmware version."""
        ...

    def test_leds(self) -> str:
        """Test all LEDs."""
        ...

    def help(self) -> str:
        """Get built-in help."""
        ...

    def measure_rate(self, channel: int = 0, duration: float = 1.0) -> RateResult:
        """Measure count rate on a single channel."""
        ...

    def measure_coincidence_rate(
        self,
        duration: float = 1.0,
        singles_a_channel: int = 0,
        singles_b_channel: int = 1,
        coincidence_channel: int = 4,
        coincidence_window: float = 25e-9,
    ) -> CoincidenceResult:
        """Measure coincidence rate with accidental correction."""
        ...


@runtime_checkable
class SettingsApplicable(Protocol):
    """
    Protocol for objects that can have device settings applied.

    This is used by the unified settings application logic.
    """

    def set_channel(self, channel: int, A: int = 0, B: int = 0, C: int = 0, D: int = 0) -> str:
        """Configure which inputs a counter watches."""
        ...

    def set_trigger_level(self, voltage: float) -> str:
        """Set trigger level voltage."""
        ...

    def set_impedance_50ohm(self) -> str:
        """Set input impedance to 50 Ohms."""
        ...

    def set_impedance_highz(self) -> str:
        """Set input impedance to high-Z."""
        ...

    def set_dac_voltage(self, voltage: float) -> str:
        """Set DAC output voltage."""
        ...
