"""
CD48 Coincidence Counter Interface

This module provides a Python interface for the Red Dog Physics CD48
Coincidence Counter using PySerial for USB communication.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Literal, TypedDict, overload

import serial
import serial.tools.list_ports


class CD48Error(Exception):
    """Base exception for CD48 errors."""

    pass


class CD48ParseError(CD48Error):
    """Raised when device response cannot be parsed."""

    pass


class CD48DeviceNotFoundError(CD48Error):
    """Raised when CD48 device cannot be found."""

    pass


class CD48ConnectionError(CD48Error):
    """Raised when connection to CD48 fails or is lost."""

    pass


class CD48ConfigError(CD48Error):
    """Raised when configuration file is invalid."""

    pass


class CD48ResponseError(CD48Error):
    """Raised when device response validation fails in strict mode."""

    pass


# Type aliases for callbacks
DisconnectCallback = Callable[[], None]
ReconnectCallback = Callable[[], None]


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

    # Commands that expect numeric/data responses (not just OK)
    _DATA_COMMANDS: set[str] = {"c", "C", "p", "P", "E", "v", "H"}

    # Commands that modify settings (expect acknowledgment)
    _SETTING_COMMANDS: set[str] = {"S", "L", "z", "Z", "r", "R", "V", "T"}

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        init_delay: float | None = None,
        strict_mode: bool = False,
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
            Read timeout in seconds (default 1.0). Increase if experiencing
            timeout errors on slower systems.
        init_delay : float, optional
            Device initialization delay in seconds (default: INIT_DELAY).
            Set to 0 to skip delay (useful for reconnecting to already-initialized device).
        strict_mode : bool
            If True, validates device responses more thoroughly (default False).
            In strict mode:
            - Checks for non-empty responses
            - Validates response format for data commands
            - Raises CD48ResponseError on unexpected responses
        """
        self._logger = logging.getLogger(__name__)
        self._init_delay = init_delay if init_delay is not None else self.INIT_DELAY
        self._strict_mode = strict_mode

        if port is None:
            port = self._find_cd48()

        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout

        self.ser: serial.Serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        if self._init_delay > 0:
            time.sleep(self._init_delay)
        self.ser.reset_input_buffer()

    @classmethod
    def from_config(
        cls,
        config_path: str | Path,
        apply_settings: bool = True,
    ) -> CD48:
        """
        Create a CD48 instance from a configuration file.

        Supports both JSON and YAML configuration files. YAML support requires
        the PyYAML package to be installed.

        Parameters:
        -----------
        config_path : str or Path
            Path to the configuration file (.json or .yaml/.yml)
        apply_settings : bool
            If True, apply device settings from config after connecting (default True)

        Returns:
        --------
        CD48 : Configured CD48 instance

        Configuration file format:
        --------------------------
        {
            "connection": {
                "port": "/dev/ttyUSB0",  // optional, auto-detect if not specified
                "baudrate": 115200,       // optional, default 115200
                "timeout": 1.0,           // optional, default 1.0
                "init_delay": 2.0         // optional, default 2.0
            },
            "settings": {
                "trigger_level": 1.5,     // voltage in V
                "impedance": "50ohm",     // "50ohm" or "highz"
                "dac_voltage": 2.0,       // voltage in V
                "channels": {
                    "0": {"A": 1, "B": 0, "C": 0, "D": 0},
                    "4": {"A": 1, "B": 1, "C": 0, "D": 0}
                }
            }
        }

        Raises:
        -------
        CD48ConfigError
            If configuration file is invalid or cannot be parsed
        FileNotFoundError
            If configuration file does not exist
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        config = cls._load_config_file(config_path)

        # Extract connection settings
        connection_raw = config.get("connection", {})
        connection = connection_raw if isinstance(connection_raw, dict) else {}

        port_val = connection.get("port")
        port: str | None = str(port_val) if port_val is not None else None

        baudrate_val = connection.get("baudrate", cls.DEFAULT_BAUDRATE)
        baudrate: int = (
            int(baudrate_val) if isinstance(baudrate_val, (int, float)) else cls.DEFAULT_BAUDRATE
        )

        timeout_val = connection.get("timeout", cls.DEFAULT_TIMEOUT)
        timeout: float = (
            float(timeout_val) if isinstance(timeout_val, (int, float)) else cls.DEFAULT_TIMEOUT
        )

        init_delay_val = connection.get("init_delay")
        init_delay: float | None = (
            float(init_delay_val) if isinstance(init_delay_val, (int, float)) else None
        )

        strict_mode_val = connection.get("strict_mode", False)
        strict_mode: bool = bool(strict_mode_val) if strict_mode_val is not None else False

        # Create instance
        instance = cls(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            init_delay=init_delay,
            strict_mode=strict_mode,
        )

        # Apply device settings if requested
        if apply_settings:
            settings_raw = config.get("settings", {})
            settings = settings_raw if isinstance(settings_raw, dict) else {}
            instance._apply_config_settings(settings)

        return instance

    @staticmethod
    def _load_config_file(config_path: Path) -> dict[str, object]:
        """Load configuration from JSON or YAML file."""
        suffix = config_path.suffix.lower()

        with open(config_path, encoding="utf-8") as f:
            if suffix == ".json":
                try:
                    result: dict[str, object] = json.load(f)
                    return result
                except json.JSONDecodeError as e:
                    raise CD48ConfigError(f"Invalid JSON in config file: {e}") from e
            elif suffix in (".yaml", ".yml"):
                try:
                    import yaml  # type: ignore[import-untyped]
                except ImportError as e:
                    raise CD48ConfigError(
                        "PyYAML is required for YAML config files. "
                        "Install with: pip install pyyaml"
                    ) from e
                try:
                    result = yaml.safe_load(f)
                    return result if result is not None else {}
                except yaml.YAMLError as e:
                    raise CD48ConfigError(f"Invalid YAML in config file: {e}") from e
            else:
                raise CD48ConfigError(
                    f"Unsupported config file format: {suffix}. Use .json or .yaml/.yml"
                )

    def _apply_config_settings(self, settings: dict[str, object]) -> None:
        """Apply device settings from configuration."""
        # Set trigger level
        if "trigger_level" in settings:
            trigger = settings["trigger_level"]
            if isinstance(trigger, (int, float)):
                self.set_trigger_level(float(trigger))

        # Set impedance
        if "impedance" in settings:
            impedance = settings["impedance"]
            if impedance == "50ohm":
                self.set_impedance_50ohm()
            elif impedance == "highz":
                self.set_impedance_highz()
            else:
                self._logger.warning(f"Unknown impedance setting: {impedance}")

        # Set DAC voltage
        if "dac_voltage" in settings:
            dac = settings["dac_voltage"]
            if isinstance(dac, (int, float)):
                self.set_dac_voltage(float(dac))

        # Configure channels
        if "channels" in settings:
            channels = settings["channels"]
            if isinstance(channels, dict):
                for ch_str, ch_config in channels.items():
                    try:
                        ch_num = int(ch_str)
                        if isinstance(ch_config, dict):
                            self.set_channel(
                                ch_num,
                                A=int(ch_config.get("A", 0)),
                                B=int(ch_config.get("B", 0)),
                                C=int(ch_config.get("C", 0)),
                                D=int(ch_config.get("D", 0)),
                            )
                    except (ValueError, TypeError) as e:
                        self._logger.warning(f"Invalid channel config {ch_str}: {e}")

    @property
    def is_connected(self) -> bool:
        """Return True if connected to the device."""
        return self.ser is not None and self.ser.is_open

    @property
    def port(self) -> str | None:
        """Return the serial port name."""
        return self._port

    @property
    def strict_mode(self) -> bool:
        """Return True if strict response validation is enabled."""
        return self._strict_mode

    @strict_mode.setter
    def strict_mode(self, value: bool) -> None:
        """Enable or disable strict response validation."""
        self._strict_mode = value

    def reconnect(self, init_delay: float | None = None) -> None:
        """
        Reconnect to the CD48 device.

        Closes the existing connection and establishes a new one.
        Useful for recovering from connection errors or device resets.

        Parameters:
        -----------
        init_delay : float, optional
            Device initialization delay in seconds. If None, uses 0 (skip delay)
            since device should already be initialized.

        Raises:
        -------
        CD48DeviceNotFoundError
            If the device cannot be found
        CD48ConnectionError
            If reconnection fails
        """
        # Close existing connection
        try:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass  # Ignore errors when closing broken connection

        # Determine port
        port = self._port if self._port is not None else self._find_cd48()

        # Reconnect with minimal delay (device already initialized)
        delay = init_delay if init_delay is not None else 0

        try:
            self.ser = serial.Serial(port, baudrate=self._baudrate, timeout=self._timeout)
            if delay > 0:
                time.sleep(delay)
            self.ser.reset_input_buffer()
            self._logger.info(f"Reconnected to CD48 on {port}")
        except serial.SerialException as e:
            raise CD48ConnectionError(f"Failed to reconnect to CD48: {e}") from e

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
        """Send command and return response."""
        self.ser.write((command + "\r").encode())
        time.sleep(self.COMMAND_DELAY)
        response: str = self.ser.read_all().decode().strip()

        if self._strict_mode:
            self._validate_response(command, response)

        return response

    def _validate_response(self, command: str, response: str) -> None:
        """
        Validate device response in strict mode.

        Parameters:
        -----------
        command : str
            The command that was sent
        response : str
            The response received from the device

        Raises:
        -------
        CD48ResponseError
            If response validation fails
        """
        # Check for empty response
        if not response:
            raise CD48ResponseError(f"Empty response for command '{command}'")

        # Extract command letter (first character, ignoring parameters)
        cmd_char = command[0] if command else ""

        # Validate data commands - should return data, not error
        if cmd_char in self._DATA_COMMANDS:
            # 'c' command should return space-separated numbers
            if cmd_char == "c":
                parts = response.split()
                if len(parts) < self.NUM_CHANNELS + 1:
                    raise CD48ResponseError(
                        f"Invalid counts response format: expected {self.NUM_CHANNELS + 1} "
                        f"values, got {len(parts)}: '{response}'"
                    )
                # Verify all parts are numeric
                for i, part in enumerate(parts[: self.NUM_CHANNELS + 1]):
                    if not part.lstrip("-").isdigit():
                        raise CD48ResponseError(
                            f"Non-numeric value in counts response at position {i}: '{part}'"
                        )

            # 'E' command should return a single integer (overflow status)
            elif cmd_char == "E":
                if not response.strip().lstrip("-").isdigit():
                    raise CD48ResponseError(
                        f"Invalid overflow response: expected integer, got '{response}'"
                    )

        # Log response for setting commands if debug logging is enabled
        elif cmd_char.upper() in {c.upper() for c in self._SETTING_COMMANDS}:
            self._logger.debug(f"Command '{command}' response: '{response}'")

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
                    counts = [int(x) for x in parts[: self.NUM_CHANNELS]]
                    overflow = int(parts[self.NUM_CHANNELS])
                    return {"counts": counts, "overflow": overflow}
                except ValueError as e:
                    raise CD48ParseError(f"Failed to parse counts response: {response}") from e
            raise CD48ParseError(f"Unexpected response format: {response}")

    @overload
    def read_and_clear_counts(self, human_readable: Literal[True] = True) -> str: ...

    @overload
    def read_and_clear_counts(self, human_readable: Literal[False]) -> CountsDict: ...

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
        if human_readable:
            return self.get_counts(human_readable=True)
        else:
            return self.get_counts(human_readable=False)

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
        interval_ms = max(
            self.REPEAT_INTERVAL_MIN_MS, min(self.REPEAT_INTERVAL_MAX_MS, interval_ms)
        )
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

    def __enter__(self) -> CD48:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()


class CD48WithReconnect(CD48):
    """CD48 with automatic reconnection support.

    This class extends CD48 with automatic reconnection when the device
    disconnects unexpectedly. Useful for long-running experiments where
    USB connections may be temporarily lost.

    Example:
    --------
    >>> def on_disconnect():
    ...     print("Device disconnected!")
    >>> def on_reconnect():
    ...     print("Device reconnected!")
    >>> with CD48WithReconnect(
    ...     on_disconnect=on_disconnect,
    ...     on_reconnect=on_reconnect
    ... ) as cd48:
    ...     result = cd48.measure_rate(channel=0, duration=1.0)
    """

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = CD48.DEFAULT_BAUDRATE,
        timeout: float = CD48.DEFAULT_TIMEOUT,
        init_delay: float | None = None,
        strict_mode: bool = False,
        auto_reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_reconnect_attempts: int = 5,
        on_disconnect: DisconnectCallback | None = None,
        on_reconnect: ReconnectCallback | None = None,
    ) -> None:
        """
        Initialize CD48 with reconnection support.

        Parameters:
        -----------
        port : str, optional
            Serial port name
        baudrate : int
            Communication speed (default 115200)
        timeout : float
            Read timeout in seconds
        init_delay : float, optional
            Device initialization delay in seconds
        strict_mode : bool
            If True, validates device responses more thoroughly (default False)
        auto_reconnect : bool
            If True, automatically attempt to reconnect on disconnect (default True)
        reconnect_delay : float
            Delay between reconnection attempts in seconds (default 1.0)
        max_reconnect_attempts : int
            Maximum number of reconnection attempts (default 5)
        on_disconnect : callable, optional
            Callback function called when device disconnects
        on_reconnect : callable, optional
            Callback function called when device reconnects
        """
        super().__init__(port, baudrate, timeout, init_delay, strict_mode)
        self._auto_reconnect = auto_reconnect
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_attempts = max_reconnect_attempts
        self._on_disconnect = on_disconnect
        self._on_reconnect = on_reconnect

    def _handle_disconnect(self) -> None:
        """Handle device disconnection."""
        if self._on_disconnect is not None:
            self._on_disconnect()
        self._logger.warning("CD48 device disconnected")

    def try_reconnect(self) -> bool:
        """
        Attempt to reconnect to the device with retries.

        Uses exponential backoff between attempts.

        Returns:
        --------
        bool : True if reconnection successful, False otherwise
        """
        for attempt in range(1, self._max_reconnect_attempts + 1):
            self._logger.info(f"Reconnection attempt {attempt}/{self._max_reconnect_attempts}")

            try:
                self.reconnect()

                if self._on_reconnect is not None:
                    self._on_reconnect()

                return True

            except (CD48DeviceNotFoundError, CD48ConnectionError, OSError) as e:
                self._logger.warning(f"Reconnection attempt {attempt} failed: {e}")
                if attempt < self._max_reconnect_attempts:
                    time.sleep(self._reconnect_delay * attempt)  # Exponential backoff

        self._logger.error(f"Failed to reconnect after {self._max_reconnect_attempts} attempts")
        return False

    def _send_command(self, command: str) -> str:
        """Send command with automatic reconnection on failure."""
        try:
            return super()._send_command(command)
        except (OSError, serial.SerialException) as e:
            if not self._auto_reconnect:
                raise CD48ConnectionError(f"Command failed: {e}") from e

            self._handle_disconnect()
            if self.try_reconnect():
                # Retry command after reconnection
                try:
                    return super()._send_command(command)
                except (OSError, serial.SerialException) as retry_error:
                    raise CD48ConnectionError(
                        f"Command failed after reconnection: {retry_error}"
                    ) from retry_error
            raise CD48ConnectionError(f"Command failed and reconnection unsuccessful: {e}") from e
