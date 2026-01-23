"""
Hardware constants and configuration defaults for CD48.

This module centralizes all hardware-related constants used across
the sync and async CD48 implementations.
"""

from __future__ import annotations

# =============================================================================
# Device Timing Constants
# =============================================================================

# Device initialization delay in seconds. The CD48 uses a Cypress PSoC5 chip
# which requires time to enumerate the USB interface and initialize the serial
# buffer after connection. 2 seconds is conservative; 1 second may work.
INIT_DELAY: float = 2.0

# Command response delay in seconds. Small delay after sending a command
# to allow the device firmware to process and respond. 50ms is sufficient
# for most commands.
COMMAND_DELAY: float = 0.05

# =============================================================================
# Hardware Identification
# =============================================================================

# USB Vendor ID for Cypress PSoC5 chip used in CD48
CYPRESS_VENDOR_ID: int = 0x04B4

# USB Product ID for Cypress PSoC5 chip (used in some detection modes)
CYPRESS_PRODUCT_ID: int = 0x8613

# =============================================================================
# Channel Configuration
# =============================================================================

# Number of counters/channels available on the CD48 device
NUM_CHANNELS: int = 8

# =============================================================================
# DAC Configuration
# =============================================================================

# DAC voltage range: The CD48 uses an 8-bit DAC with a 0-4.08V output range
# Maximum output voltage in volts
DAC_MAX_VOLTAGE: float = 4.08

# Maximum byte value for 8-bit DAC
DAC_MAX_BYTE: int = 255

# =============================================================================
# Auto-repeat Interval Limits
# =============================================================================

# Minimum interval to prevent overwhelming the USB interface (milliseconds)
REPEAT_INTERVAL_MIN_MS: int = 100

# Maximum interval - 16-bit unsigned integer limit (milliseconds)
REPEAT_INTERVAL_MAX_MS: int = 65535

# =============================================================================
# Communication Defaults
# =============================================================================

# Default baud rate for USB serial communication
DEFAULT_BAUDRATE: int = 115200

# Default timeout for serial read operations in seconds
DEFAULT_TIMEOUT: float = 1.0

# =============================================================================
# Physics Constants
# =============================================================================

# Default coincidence window in seconds (25 nanoseconds)
# This is the time window for counting coincident events
DEFAULT_COINCIDENCE_WINDOW: float = 25e-9

# =============================================================================
# Command Categories
# =============================================================================

# Commands that expect numeric/data responses (not just OK)
DATA_COMMANDS: frozenset[str] = frozenset({"c", "C", "p", "P", "E", "v", "H"})

# Commands that modify settings (expect acknowledgment)
SETTING_COMMANDS: frozenset[str] = frozenset({"S", "L", "z", "Z", "r", "R", "V", "T"})
