"""
Async CD48 Coincidence Counter Interface

This module provides an asynchronous Python interface for the Red Dog Physics CD48
Coincidence Counter using aioserial for non-blocking USB communication.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from types import TracebackType
from typing import TYPE_CHECKING, Literal, overload

from .cd48 import CD48Error, CD48ParseError
from .constants import (
    COMMAND_DELAY,
    CYPRESS_VENDOR_ID,
    DAC_MAX_BYTE,
    DAC_MAX_VOLTAGE,
    DEFAULT_BAUDRATE,
    DEFAULT_COINCIDENCE_WINDOW,
    DEFAULT_TIMEOUT,
    INIT_DELAY,
    NUM_CHANNELS,
    REPEAT_INTERVAL_MAX_MS,
    REPEAT_INTERVAL_MIN_MS,
)
from .protocols import CoincidenceResult, CountsDict, RateResult
from .utils import (
    CD48DeviceNotFoundError,
    find_cd48_port,
    validate_binary_input,
    validate_channel,
    voltage_to_dac_byte,
)

if TYPE_CHECKING:
    import aioserial


class AsyncCD48:
    """Async interface for Red Dog Physics CD48 Coincidence Counter.

    This class provides the same functionality as CD48 but with async/await support
    for non-blocking I/O operations. Useful for GUI applications and concurrent
    measurement scenarios.

    Example:
    --------
    >>> async with AsyncCD48() as cd48:
    ...     result = await cd48.measure_rate(channel=0, duration=1.0)
    ...     print(f"Rate: {result['rate']:.2f} Hz")
    """

    # Re-export constants as class attributes for backward compatibility
    INIT_DELAY: float = INIT_DELAY
    COMMAND_DELAY: float = COMMAND_DELAY
    CYPRESS_VENDOR_ID: int = CYPRESS_VENDOR_ID
    NUM_CHANNELS: int = NUM_CHANNELS
    DAC_MAX_VOLTAGE: float = DAC_MAX_VOLTAGE
    DAC_MAX_BYTE: int = DAC_MAX_BYTE
    REPEAT_INTERVAL_MIN_MS: int = REPEAT_INTERVAL_MIN_MS
    REPEAT_INTERVAL_MAX_MS: int = REPEAT_INTERVAL_MAX_MS
    DEFAULT_BAUDRATE: int = DEFAULT_BAUDRATE
    DEFAULT_TIMEOUT: float = DEFAULT_TIMEOUT
    DEFAULT_COINCIDENCE_WINDOW: float = DEFAULT_COINCIDENCE_WINDOW

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        init_delay: float | None = None,
    ) -> None:
        """
        Initialize async connection to CD48.

        Note: The actual connection is established when entering the async context
        manager or by calling connect() explicitly.

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
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._init_delay = init_delay if init_delay is not None else INIT_DELAY
        self._ser: aioserial.AioSerial | None = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish async connection to the CD48 device.

        This method is called automatically when using the async context manager.

        Raises:
        -------
        CD48DeviceNotFoundError
            If auto-detection fails and no port is specified
        ImportError
            If aioserial is not installed
        """
        try:
            import aioserial as aio
        except ImportError as e:
            raise ImportError(
                "aioserial is required for async support. Install with: pip install aioserial"
            ) from e

        port = self._port if self._port is not None else find_cd48_port(logger=self._logger)
        self._ser = aio.AioSerial(port=port, baudrate=self._baudrate, timeout=self._timeout)

        if self._init_delay > 0:
            await asyncio.sleep(self._init_delay)

        self._ser.reset_input_buffer()
        self._connected = True
        self._logger.info(f"Connected to CD48 on {port}")

    @property
    def is_connected(self) -> bool:
        """Return True if connected to the device."""
        return self._connected and self._ser is not None and self._ser.is_open

    @property
    def port(self) -> str | None:
        """Return the serial port name."""
        if self._ser is not None:
            return str(self._ser.port)
        return self._port

    async def _send_command(self, command: str) -> str:
        """Send command and return response asynchronously."""
        if self._ser is None or not self._connected:
            raise CD48Error("Not connected to CD48. Call connect() first.")

        await self._ser.write_async((command + "\r").encode())
        await asyncio.sleep(self.COMMAND_DELAY)
        response_bytes: bytes = await self._ser.read_async(self._ser.in_waiting or 1024)
        response: str = response_bytes.decode().strip()
        return response

    @overload
    async def get_counts(self, human_readable: Literal[True] = True) -> str: ...

    @overload
    async def get_counts(self, human_readable: Literal[False]) -> CountsDict: ...

    async def get_counts(self, human_readable: bool = True) -> str | CountsDict:
        """
        Get current counts from all channels and reset counters to zero.

        Parameters:
        -----------
        human_readable : bool
            If True, uses 'C' command (formatted). If False, uses 'c' (parseable)

        Returns:
        --------
        str or dict : Raw response string or parsed dict with counts and overflow
        """
        if human_readable:
            return await self._send_command("C")
        else:
            response = await self._send_command("c")
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
    async def read_and_clear_counts(self, human_readable: Literal[True] = True) -> str: ...

    @overload
    async def read_and_clear_counts(self, human_readable: Literal[False]) -> CountsDict: ...

    async def read_and_clear_counts(self, human_readable: bool = True) -> str | CountsDict:
        """Read current counts and clear counters (explicit alias for get_counts)."""
        if human_readable:
            return await self.get_counts(human_readable=True)
        else:
            return await self.get_counts(human_readable=False)

    async def clear_counts(self) -> None:
        """Clear all counters by reading and discarding the values."""
        await self.get_counts(human_readable=False)

    async def set_channel(
        self, channel: int, A: int = 0, B: int = 0, C: int = 0, D: int = 0
    ) -> str:
        """
        Configure which inputs a counter watches.

        Parameters:
        -----------
        channel : int (0-7)
            Counter number to configure
        A, B, C, D : int (0 or 1)
            Which inputs to monitor (1=on, 0=off)
        """
        validate_channel(channel)
        for name, value in [("A", A), ("B", B), ("C", C), ("D", D)]:
            validate_binary_input(name, value)
        command = f"S{channel}{A}{B}{C}{D}"
        return await self._send_command(command)

    async def set_trigger_level(self, voltage: float) -> str:
        """Set trigger level voltage (0.0 to 4.08V)."""
        byte_val = voltage_to_dac_byte(voltage)
        return await self._send_command(f"L{byte_val}")

    async def set_impedance_50ohm(self) -> str:
        """Set input impedance to 50 Ohms."""
        return await self._send_command("z")

    async def set_impedance_highz(self) -> str:
        """Set input impedance to high-Z."""
        return await self._send_command("Z")

    async def set_repeat(self, interval_ms: int) -> str:
        """Set automatic count reporting interval (100-65535 ms)."""
        interval_ms = max(
            self.REPEAT_INTERVAL_MIN_MS, min(self.REPEAT_INTERVAL_MAX_MS, interval_ms)
        )
        return await self._send_command(f"r{interval_ms}")

    async def toggle_repeat(self) -> str:
        """Toggle automatic repeat reporting on/off."""
        return await self._send_command("R")

    async def get_settings(self, human_readable: bool = True) -> str:
        """Get all current settings."""
        if human_readable:
            return await self._send_command("P")
        else:
            return await self._send_command("p")

    async def get_overflow(self) -> int:
        """Check and clear overflow status."""
        response = await self._send_command("E")
        try:
            return int(response.strip())
        except ValueError as e:
            raise CD48ParseError(f"Failed to parse overflow response: {response}") from e

    async def set_dac_voltage(self, voltage: float) -> str:
        """Set DAC output voltage (0.0 to 4.08V)."""
        byte_val = voltage_to_dac_byte(voltage)
        return await self._send_command(f"V{byte_val}")

    async def get_version(self) -> str:
        """Get firmware version."""
        return await self._send_command("v")

    async def test_leds(self) -> str:
        """Test all LEDs (turns on for 1 second)."""
        return await self._send_command("T")

    async def help(self) -> str:
        """Get built-in help."""
        return await self._send_command("H")

    async def close(self) -> None:
        """Close serial connection."""
        if self._ser is not None:
            self._ser.close()
            self._connected = False
            self._logger.info("Disconnected from CD48")

    # High-level measurement methods

    async def measure_rate(self, channel: int = 0, duration: float = 1.0) -> RateResult:
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
        """
        validate_channel(channel)

        await self.clear_counts()
        await asyncio.sleep(duration)
        data = await self.get_counts(human_readable=False)
        counts = data["counts"][channel]

        return {
            "counts": counts,
            "duration": duration,
            "rate": counts / duration,
            "channel": channel,
        }

    async def measure_coincidence_rate(
        self,
        duration: float = 1.0,
        singles_a_channel: int = 0,
        singles_b_channel: int = 1,
        coincidence_channel: int = 4,
        coincidence_window: float = DEFAULT_COINCIDENCE_WINDOW,
    ) -> CoincidenceResult:
        """
        Measure coincidence rate with accidental correction.

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
        """
        await self.clear_counts()
        await asyncio.sleep(duration)
        data = await self.get_counts(human_readable=False)

        singles_a = data["counts"][singles_a_channel]
        singles_b = data["counts"][singles_b_channel]
        coincidences = data["counts"][coincidence_channel]

        rate_a = singles_a / duration
        rate_b = singles_b / duration
        coincidence_rate = coincidences / duration

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

    async def __aenter__(self) -> AsyncCD48:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()


# Type alias for disconnect callback
DisconnectCallback = Callable[[], None]
ReconnectCallback = Callable[[], None]


class AsyncCD48WithReconnect(AsyncCD48):
    """AsyncCD48 with automatic reconnection support.

    This class extends AsyncCD48 with automatic reconnection when the device
    disconnects unexpectedly. Useful for long-running experiments.

    Example:
    --------
    >>> def on_disconnect():
    ...     print("Device disconnected!")
    >>> def on_reconnect():
    ...     print("Device reconnected!")
    >>> async with AsyncCD48WithReconnect(
    ...     on_disconnect=on_disconnect,
    ...     on_reconnect=on_reconnect
    ... ) as cd48:
    ...     result = await cd48.measure_rate(channel=0, duration=1.0)
    """

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = AsyncCD48.DEFAULT_BAUDRATE,
        timeout: float = AsyncCD48.DEFAULT_TIMEOUT,
        init_delay: float | None = None,
        auto_reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_reconnect_attempts: int = 5,
        on_disconnect: DisconnectCallback | None = None,
        on_reconnect: ReconnectCallback | None = None,
    ) -> None:
        """
        Initialize AsyncCD48 with reconnection support.

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
        super().__init__(port, baudrate, timeout, init_delay)
        self._auto_reconnect = auto_reconnect
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_attempts = max_reconnect_attempts
        self._on_disconnect = on_disconnect
        self._on_reconnect = on_reconnect
        self._reconnect_attempts = 0

    async def _handle_disconnect(self) -> None:
        """Handle device disconnection."""
        self._connected = False
        if self._on_disconnect is not None:
            self._on_disconnect()
        self._logger.warning("CD48 device disconnected")

    async def reconnect(self) -> bool:
        """
        Attempt to reconnect to the device.

        Returns:
        --------
        bool : True if reconnection successful, False otherwise
        """
        self._reconnect_attempts = 0

        while self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            self._logger.info(
                f"Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}"
            )

            try:
                if self._ser is not None:
                    with contextlib.suppress(Exception):
                        self._ser.close()

                await self.connect()

                if self._on_reconnect is not None:
                    self._on_reconnect()

                self._reconnect_attempts = 0
                return True

            except (CD48DeviceNotFoundError, OSError) as e:
                self._logger.warning(f"Reconnection failed: {e}")
                await asyncio.sleep(self._reconnect_delay)

        self._logger.error(f"Failed to reconnect after {self._max_reconnect_attempts} attempts")
        return False

    async def _send_command(self, command: str) -> str:
        """Send command with automatic reconnection on failure."""
        try:
            return await super()._send_command(command)
        except (OSError, CD48Error) as e:
            if not self._auto_reconnect:
                raise

            await self._handle_disconnect()
            if await self.reconnect():
                # Retry command after reconnection
                try:
                    return await super()._send_command(command)
                except (OSError, CD48Error) as retry_error:
                    raise CD48Error(
                        f"Command failed after reconnection: {retry_error}"
                    ) from retry_error
            raise CD48Error(f"Command failed and reconnection unsuccessful: {e}") from e
