"""
CD48 Coincidence Counter Interface

This module provides a Python interface for the Red Dog Physics CD48
Coincidence Counter using PySerial for USB communication.
"""

from typing import Optional, Union, Dict, List, Any, cast, overload, Literal, TypedDict
import serial
import serial.tools.list_ports
import time


class CountsDict(TypedDict):
    """Type definition for parsed counts data."""
    counts: List[int]
    overflow: int


class CD48:
    """Interface for Red Dog Physics CD48 Coincidence Counter"""

    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 1) -> None:
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
        """
        if port is None:
            port = self._find_cd48()

        self.ser: serial.Serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        time.sleep(2)  # Give device time to initialize
        self.ser.reset_input_buffer()

    def _find_cd48(self) -> str:
        """Attempt to auto-detect CD48 on serial ports"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # CD48 uses Cypress PSoC5 chip - look for relevant identifiers
            if 'USB' in port.description or 'Serial' in port.description:
                print(f"Found potential device: {port.device} - {port.description}")
                return cast(str, port.device)
        raise ValueError("Could not find CD48. Please specify port manually.")

    def _send_command(self, command: str) -> str:
        """Send command and return response"""
        self.ser.write((command + '\r').encode())
        time.sleep(0.05)  # Small delay for device to respond
        response: str = self.ser.read_all().decode().strip()
        return response

    @overload
    def get_counts(self, human_readable: Literal[True] = True) -> str: ...

    @overload
    def get_counts(self, human_readable: Literal[False]) -> CountsDict: ...

    def get_counts(self, human_readable: bool = True) -> Union[str, CountsDict]:
        """
        Get current counts from all channels

        Parameters:
        -----------
        human_readable : bool
            If True, uses 'C' command (formatted). If False, uses 'c' (parseable)

        Returns:
        --------
        str or dict : Raw response string or parsed dict with counts and overflow
        """
        if human_readable:
            return self._send_command('C')
        else:
            response = self._send_command('c')
            # Parse space-delimited response: 8 counts + overflow status
            parts = response.split()
            if len(parts) >= 9:
                counts = [int(x) for x in parts[:8]]
                overflow = int(parts[8])
                return {'counts': counts, 'overflow': overflow}
            return response

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
        """
        command = f'S{channel}{A}{B}{C}{D}'
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
        return self._send_command(f'L{byte_val}')

    def set_impedance_50ohm(self) -> str:
        """Set input impedance to 50 Ohms"""
        return self._send_command('z')

    def set_impedance_highz(self) -> str:
        """Set input impedance to high-Z"""
        return self._send_command('Z')

    def set_repeat(self, interval_ms: int) -> str:
        """
        Set automatic count reporting interval

        Parameters:
        -----------
        interval_ms : int
            Reporting interval in milliseconds (100-65535)
        """
        interval_ms = max(100, min(65535, interval_ms))
        return self._send_command(f'r{interval_ms}')

    def toggle_repeat(self) -> str:
        """Toggle automatic repeat reporting on/off"""
        return self._send_command('R')

    def get_settings(self, human_readable: bool = True) -> str:
        """Get all current settings"""
        if human_readable:
            return self._send_command('P')
        else:
            return self._send_command('p')

    def get_overflow(self) -> Union[int, str]:
        """
        Check and clear overflow status

        Returns:
        --------
        int : 8-bit overflow flag (bit n indicates counter n overflowed)
        """
        response = self._send_command('E')
        try:
            return int(response.strip())
        except:
            return response

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
        return self._send_command(f'V{byte_val}')

    def get_version(self) -> str:
        """Get firmware version"""
        return self._send_command('v')

    def test_leds(self) -> str:
        """Test all LEDs (turns on for 1 second)"""
        return self._send_command('T')

    def help(self) -> str:
        """Get built-in help"""
        return self._send_command('H')

    def close(self) -> None:
        """Close serial connection"""
        self.ser.close()

    def __enter__(self) -> 'CD48':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
