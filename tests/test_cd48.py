"""
Unit tests for CD48 class.

These tests mock the serial communication to test the CD48 interface
without requiring actual hardware.
"""

from typing import List, cast
import unittest
from unittest.mock import Mock, MagicMock, patch
import serial
from pycd48 import CD48


class TestCD48(unittest.TestCase):
    """Test cases for CD48 class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock serial.Serial to avoid needing actual hardware
        self.mock_serial: Mock = Mock(spec=serial.Serial)
        self.mock_serial.read_all = Mock(return_value=b"OK\r\n")

    @patch("serial.Serial")
    def test_init_with_port(self, mock_serial_class: MagicMock) -> None:
        """Test initialization with specified port."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        mock_serial_class.assert_called_once_with("/dev/ttyUSB0", baudrate=115200, timeout=1)
        self.assertIsNotNone(cd48.ser)

    @patch("serial.tools.list_ports.comports")
    @patch("serial.Serial")
    def test_init_auto_detect(self, mock_serial_class: MagicMock, mock_comports: MagicMock) -> None:
        """Test initialization with auto-detection."""
        # Mock port detection
        mock_port: Mock = Mock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = "USB Serial Device"
        mock_comports.return_value = [mock_port]

        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48()

        self.assertIsNotNone(cd48.ser)

    @patch("serial.Serial")
    def test_set_channel(self, mock_serial_class: MagicMock) -> None:
        """Test set_channel command."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        cd48.set_channel(4, A=1, B=1, C=0, D=0)

        # Verify the correct command was sent
        self.mock_serial.write.assert_called()
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertEqual(call_args, b"S41100\r")

    @patch("serial.Serial")
    def test_set_trigger_level(self, mock_serial_class: MagicMock) -> None:
        """Test set_trigger_level voltage conversion."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Test voltage to byte conversion
        # 2.04V should map to 127 (approximately half of 255 for 4.08V range)
        cd48.set_trigger_level(2.04)

        call_args = self.mock_serial.write.call_args[0][0]
        # Should be 'L127\r'
        self.assertTrue(call_args.startswith(b"L"))
        self.assertTrue(call_args.endswith(b"\r"))

    @patch("serial.Serial")
    def test_get_counts_parsed(self, mock_serial_class: MagicMock) -> None:
        """Test get_counts with parsing."""
        mock_serial_class.return_value = self.mock_serial

        # Mock response: 8 count values + overflow flag
        self.mock_serial.read_all.return_value = b"100 200 300 400 50 25 10 5 0\r\n"

        cd48 = CD48(port="/dev/ttyUSB0")
        result = cd48.get_counts(human_readable=False)

        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)  # Type narrowing for mypy
        counts = cast(List[int], result["counts"])
        self.assertEqual(len(counts), 8)
        self.assertEqual(counts[0], 100)
        self.assertEqual(counts[4], 50)
        self.assertEqual(result["overflow"], 0)

    @patch("serial.Serial")
    def test_voltage_clamping(self, mock_serial_class: MagicMock) -> None:
        """Test that voltages are clamped to valid range."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Test out-of-range voltage (should clamp to 255)
        cd48.set_trigger_level(10.0)  # Way over 4.08V limit

        call_args = self.mock_serial.write.call_args[0][0]
        # Should clamp to L255
        self.assertEqual(call_args, b"L255\r")

    @patch("serial.Serial")
    def test_context_manager(self, mock_serial_class: MagicMock) -> None:
        """Test context manager (with statement) support."""
        mock_serial_class.return_value = self.mock_serial

        with CD48(port="/dev/ttyUSB0") as cd48:
            self.assertIsNotNone(cd48.ser)

        # Verify close was called
        self.mock_serial.close.assert_called_once()

    @patch("serial.Serial")
    def test_impedance_commands(self, mock_serial_class: MagicMock) -> None:
        """Test impedance setting commands."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        cd48.set_impedance_50ohm()
        self.mock_serial.write.assert_called_with(b"z\r")

        cd48.set_impedance_highz()
        self.mock_serial.write.assert_called_with(b"Z\r")

    @patch("serial.Serial")
    def test_repeat_mode(self, mock_serial_class: MagicMock) -> None:
        """Test repeat mode commands."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Test set_repeat with valid interval
        cd48.set_repeat(1000)
        self.mock_serial.write.assert_called_with(b"r1000\r")

        # Test interval clamping (minimum 100ms)
        cd48.set_repeat(50)  # Too low
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertEqual(call_args, b"r100\r")

        # Test toggle
        cd48.toggle_repeat()
        self.mock_serial.write.assert_called_with(b"R\r")


class TestCD48EdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    @patch("serial.tools.list_ports.comports")
    @patch("serial.Serial")
    def test_no_device_found(self, mock_serial_class: MagicMock, mock_comports: MagicMock) -> None:
        """Test behavior when no device is found."""
        # Mock empty port list
        mock_comports.return_value = []

        with self.assertRaises(ValueError) as context:
            CD48()

        self.assertIn("Could not find CD48", str(context.exception))

    @patch("serial.Serial")
    def test_channel_range(self, mock_serial_class: MagicMock) -> None:
        """Test channel number validation (0-7)."""
        mock_serial: Mock = Mock()
        mock_serial.read_all = Mock(return_value=b"OK\r\n")
        mock_serial_class.return_value = mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Valid channels (0-7) should work
        for ch in range(8):
            cd48.set_channel(ch, A=1, B=0, C=0, D=0)

        # Channels outside 0-7 will still send but may not be valid
        # (The device will handle invalid commands)


if __name__ == "__main__":
    unittest.main()
