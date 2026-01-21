"""
CD48 Coincidence Counter Interface

This module provides a Python interface for the Red Dog Physics CD48
Coincidence Counter using PySerial for USB communication.
"""

from typing import Optional, List, overload, Literal, TypedDict, Type
from types import TracebackType
import logging
import serial
import serial.tools.list_ports
import time


class CD48Error(Exception):
    """Base exception for CD48 errors."""

    pass


class CD48ParseError(CD48Error):
    """Raised when device response cannot be parsed."""

    pass


class CD48DeviceNotFoundError(CD48Error):
    """Raised when CD48 device cannot be found."""

    pass


class CountsDict(TypedDict):
    """Type definition for parsed counts data."""

    counts: List[int]
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


class CD48:
    """Interface for Red Dog Physics CD48 Coincidence Counter"""

    # Device initialization delay in seconds. The CD48 uses a Cypress PSoC5 chip
    # which requires time to enumerate the USB interface and initialize the serial
    # buffer after connection. 2 seconds is conservative; 1 second may work.
    INIT_DELAY: float = 2.0

    # Command response delay in seconds. Small delay after sending a command
    # to allow the device firmware to process and respond. 50ms is sufficient
    # for most commands.
    COMMAND_DELAY: float = 0.05

    # Hardware constants
    # USB Vendor ID for Cypress PSoC5 chip used in CD48
    CYPRESS_VENDOR_ID: int = 0x04B4

    # Number of counters/channels available on the CD48 device
    NUM_CHANNELS: int = 8

    # DAC voltage range: The CD48 uses an 8-bit DAC with a 0-4.08V output range
    # Maximum output voltage in volts
    DAC_MAX_VOLTAGE: float = 4.08
    # Maximum byte value for 8-bit DAC
    DAC_MAX_BYTE: int = 255

    # Auto-repeat interval limits in milliseconds
    # Minimum interval to prevent overwhelming the USB interface
    REPEAT_INTERVAL_MIN_MS: int = 100
    # Maximum interval (16-bit unsigned integer limit)
    REPEAT_INTERVAL_MAX_MS: int = 65535

    # Communication defaults
    # Default baud rate for USB serial communication
    DEFAULT_BAUDRATE: int = 115200
    # Default timeout for serial read operations in seconds
    DEFAULT_TIMEOUT: float = 1.0

    # Physics constants
    # Default coincidence window in seconds (25 nanoseconds)
    # This is the time window for counting coincident events
    DEFAULT_COINCIDENCE_WINDOW: float = 25e-9

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        init_delay: Optional[float] = None,
    ) -> None:
        """
        Initialize connection to CD48

        Parameters:
        -----------
        port : str, optional
            Serial port name (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            If None, will attempt to auto-detect
        baudrate : int
            Communication speed (default 115200)
        timeout : float
            Read timeout in seconds
        init_delay : float, optional
            Device initialization delay in seconds (default: INIT_DELAY).
            Set to 0 to skip delay (useful for reconnecting to already-initialized device).
        """
        self._logger = logging.getLogger(__name__)
        self._init_delay = init_delay if init_delay is not None else self.INIT_DELAY

        if port is None:
            port = self._find_cd48()

        self.ser: serial.Serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        if self._init_delay > 0:
            time.sleep(self._init_delay)
        self.ser.reset_input_buffer()

    def _find_cd48(self) -> str:
        """Attempt to auto-detect CD48 on serial ports"""
        ports = serial.tools.list_ports.comports()

        # First pass: look for Cypress VID (more reliable)
        for port in ports:
            # CD48 uses Cypress PSoC5 chip
            if port.vid == self.CYPRESS_VENDOR_ID:
                self._logger.info(f"Found CD48 (Cypress): {port.device} - {port.description}")
                return str(port.device)

        # Second pass: fall back to description matching
        for port in ports:
            if "USB" in port.description or "Serial" in port.description:
                self._logger.info(f"Found potential device: {port.device} - {port.description}")
                return str(port.device)

        raise CD48DeviceNotFoundError("Could not find CD48. Please specify port manually.")

    def _send_command(self, command: str) -> str:
        """Send command and return response"""
        self.ser.write((command + "\r").encode())
        time.sleep(self.COMMAND_DELAY)
        response: str = self.ser.read_all().decode().strip()
        return response

    @overload
    def get_counts(self, human_readable: Literal[True] = True) -> str: ...

    @overload
    def get_counts(self, human_readable: Literal[False]) -> CountsDict: ...

    def get_counts(self, human_readable: bool = True) -> str | CountsDict:
        """
        Get current counts from all channels and reset counters to zero.

        Note: The CD48 hardware clears counters when read. This is by design
        for continuous measurement. Use read_and_clear_counts() if you want
        a method name that makes this behavior explicit.

        Parameters:
        -----------
        human_readable : bool
            If True, uses 'C' command (formatted). If False, uses 'c' (parseable)

        Returns:
        --------
        str or dict : Raw response string or parsed dict with counts and overflow

        Raises:
        -------
        CD48ParseError
            If response cannot be parsed (only when human_readable=False)
        """
        if human_readable:
            return self._send_command("C")
        else:
            response = self._send_command("c")
            # Parse space-delimited response: NUM_CHANNELS counts + overflow status
            parts = response.split()
            if len(parts) >= self.NUM_CHANNELS + 1:
                try:
                    counts = [int(x) for x in parts[:self.NUM_CHANNELS]]
                    overflow = int(parts[self.NUM_CHANNELS])
                    return {"counts": counts, "overflow": overflow}
                except ValueError as e:
                    raise CD48ParseError(f"Failed to parse counts response: {response}") from e
            raise CD48ParseError(f"Unexpected response format: {response}")

    def read_and_clear_counts(self, human_readable: bool = True) -> str | CountsDict:
        """
        Read current counts and clear counters (explicit alias for get_counts).

        This method is identical to get_counts() but with a name that makes
        the clearing behavior explicit.

        Parameters:
        -----------
        human_readable : bool
            If True, returns formatted string. If False, returns parsed dict.

        Returns:
        --------
        str or dict : Raw response string or parsed dict with counts and overflow
        """
        return self.get_counts(human_readable=human_readable)

    def clear_counts(self) -> None:
        """Clear all counters by reading and discarding the values."""
        self.get_counts(human_readable=False)

    def set_channel(self, channel: int, A: int = 0, B: int = 0, C: int = 0, D: int = 0) -> str:
        """
        Configure which inputs a counter watches

        Parameters:
        -----------
        channel : int (0-7)
            Counter number to configure
        A, B, C, D : int (0 or 1)
            Which inputs to monitor (1=on, 0=off)

        Example:
        --------
        set_channel(4, A=1, B=1, C=0, D=0)  # Counter 4 counts A-B coincidences

        Raises:
        -------
        ValueError
            If channel is not 0-7 or if A, B, C, D are not 0 or 1
        """
        if not 0 <= channel < self.NUM_CHANNELS:
            raise ValueError(f"Channel must be 0-{self.NUM_CHANNELS-1}, got {channel}")
        for name, value in [("A", A), ("B", B), ("C", C), ("D", D)]:
            if value not in (0, 1):
                raise ValueError(f"{name} must be 0 or 1, got {value}")
        command = f"S{channel}{A}{B}{C}{D}"
        return self._send_command(command)

    def set_trigger_level(self, voltage: float) -> str:
        """
        Set trigger level voltage

        Parameters:
        -----------
        voltage : float
            Voltage threshold (0.0 to 4.08V)
        """
        # Convert voltage to byte value for 8-bit DAC
        byte_val = int((voltage / self.DAC_MAX_VOLTAGE) * self.DAC_MAX_BYTE)
        # Clamp to valid range per hardware spec
        byte_val = max(0, min(self.DAC_MAX_BYTE, byte_val))
        return self._send_command(f"L{byte_val}")

    def set_impedance_50ohm(self) -> str:
        """Set input impedance to 50 Ohms"""
        return self._send_command("z")

    def set_impedance_highz(self) -> str:
        """Set input impedance to high-Z"""
        return self._send_command("Z")

    def set_repeat(self, interval_ms: int) -> str:
        """
        Set automatic count reporting interval

        Parameters:
        -----------
        interval_ms : int
            Reporting interval in milliseconds (100-65535)
        """
        interval_ms = max(self.REPEAT_INTERVAL_MIN_MS, min(self.REPEAT_INTERVAL_MAX_MS, interval_ms))
        return self._send_command(f"r{interval_ms}")

    def toggle_repeat(self) -> str:
        """Toggle automatic repeat reporting on/off"""
        return self._send_command("R")

    def get_settings(self, human_readable: bool = True) -> str:
        """Get all current settings"""
        if human_readable:
            return self._send_command("P")
        else:
            return self._send_command("p")

    def get_overflow(self) -> int:
        """
        Check and clear overflow status

        Returns:
        --------
        int : 8-bit overflow flag (bit n indicates counter n overflowed)

        Raises:
        -------
        CD48ParseError
            If response cannot be parsed as an integer
        """
        response = self._send_command("E")
        try:
            return int(response.strip())
        except ValueError as e:
            raise CD48ParseError(f"Failed to parse overflow response: {response}") from e

    def set_dac_voltage(self, voltage: float) -> str:
        """
        Set DAC output voltage

        Parameters:
        -----------
        voltage : float
            Output voltage (0.0 to 4.08V)
        """
        byte_val = int((voltage / self.DAC_MAX_VOLTAGE) * self.DAC_MAX_BYTE)
        # Clamp to valid range per hardware spec
        byte_val = max(0, min(self.DAC_MAX_BYTE, byte_val))
        return self._send_command(f"V{byte_val}")

    def get_version(self) -> str:
        """Get firmware version"""
        return self._send_command("v")

    def test_leds(self) -> str:
        """Test all LEDs (turns on for 1 second)"""
        return self._send_command("T")

    def help(self) -> str:
        """Get built-in help"""
        return self._send_command("H")

    def close(self) -> None:
        """Close serial connection"""
        self.ser.close()

    # High-level measurement methods

    def measure_rate(self, channel: int = 0, duration: float = 1.0) -> RateResult:
        """
        Measure count rate on a single channel.

        Parameters:
        -----------
        channel : int
            Channel number (0-7) to measure
        duration : float
            Measurement duration in seconds

        Returns:
        --------
        RateResult : dict with counts, duration, rate, and channel

        Example:
        --------
        >>> result = cd48.measure_rate(channel=0, duration=10)
        >>> print(f"Rate: {result['rate']:.2f} Hz")
        """
        if not 0 <= channel < self.NUM_CHANNELS:
            raise ValueError(f"Channel must be 0-{self.NUM_CHANNELS-1}, got {channel}")

        self.clear_counts()
        time.sleep(duration)
        data = self.get_counts(human_readable=False)
        counts = data["counts"][channel]

        return {
            "counts": counts,
            "duration": duration,
            "rate": counts / duration,
            "channel": channel,
        }

    def measure_coincidence_rate(
        self,
        duration: float = 1.0,
        singles_a_channel: int = 0,
        singles_b_channel: int = 1,
        coincidence_channel: int = 4,
        coincidence_window: float = DEFAULT_COINCIDENCE_WINDOW,
    ) -> CoincidenceResult:
        """
        Measure coincidence rate with accidental correction.

        Calculates true coincidence rate by subtracting expected accidentals:
            R_true = R_measured - 2 * tau * R_a * R_b

        Parameters:
        -----------
        duration : float
            Measurement duration in seconds
        singles_a_channel : int
            Channel for singles A (default: 0)
        singles_b_channel : int
            Channel for singles B (default: 1)
        coincidence_channel : int
            Channel for A+B coincidences (default: 4)
        coincidence_window : float
            Coincidence window in seconds (default: 25 ns)

        Returns:
        --------
        CoincidenceResult : dict with singles, coincidences, rates, and corrections

        Example:
        --------
        >>> result = cd48.measure_coincidence_rate(duration=60)
        >>> print(f"True coincidence rate: {result['true_coincidence_rate']:.2f} Hz")
        """
        self.clear_counts()
        time.sleep(duration)
        data = self.get_counts(human_readable=False)

        singles_a = data["counts"][singles_a_channel]
        singles_b = data["counts"][singles_b_channel]
        coincidences = data["counts"][coincidence_channel]

        rate_a = singles_a / duration
        rate_b = singles_b / duration
        coincidence_rate = coincidences / duration

        # Expected accidental coincidence rate: R_acc = 2 * tau * R_a * R_b
        accidental_rate = 2 * coincidence_window * rate_a * rate_b
        true_coincidence_rate = max(0, coincidence_rate - accidental_rate)

        return {
            "singles_a": singles_a,
            "singles_b": singles_b,
            "coincidences": coincidences,
            "duration": duration,
            "rate_a": rate_a,
            "rate_b": rate_b,
            "coincidence_rate": coincidence_rate,
            "accidental_rate": accidental_rate,
            "true_coincidence_rate": true_coincidence_rate,
        }

    def __enter__(self) -> "CD48":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()
