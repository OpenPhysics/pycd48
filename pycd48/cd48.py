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

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 1,
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
            # CD48 uses Cypress PSoC5 chip with VID 0x04b4
            if port.vid == 0x04B4:
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
        Get current counts from all channels

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
            # Parse space-delimited response: 8 counts + overflow status
            parts = response.split()
            if len(parts) >= 9:
                try:
                    counts = [int(x) for x in parts[:8]]
                    overflow = int(parts[8])
                    return {"counts": counts, "overflow": overflow}
                except ValueError as e:
                    raise CD48ParseError(f"Failed to parse counts response: {response}") from e
            raise CD48ParseError(f"Unexpected response format: {response}")

    def clear_counts(self) -> None:
        """Clear all counters by reading them"""
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
        if not 0 <= channel <= 7:
            raise ValueError(f"Channel must be 0-7, got {channel}")
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
        # Convert voltage to byte value (0-255)
        byte_val = int((voltage / 4.08) * 255)
        # Per manual: 0-255 maps to 0-4.08V
        byte_val = max(0, min(255, byte_val))  # Clamp to valid range
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
        interval_ms = max(100, min(65535, interval_ms))
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
        byte_val = int((voltage / 4.08) * 255)
        # Per manual: 0-255 maps to 0-4.08V
        byte_val = max(0, min(255, byte_val))
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

    def __enter__(self) -> "CD48":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()
