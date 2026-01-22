"""
Unit tests for CD48 class.

These tests mock the serial communication to test the CD48 interface
without requiring actual hardware.
"""

import unittest
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import serial

from pycd48 import CD48, CD48DeviceNotFoundError, CD48Error, CD48ParseError


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
        counts = cast(list[int], result["counts"])
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

        with self.assertRaises(CD48DeviceNotFoundError) as context:
            CD48()

        self.assertIn("Could not find CD48", str(context.exception))

    @patch("serial.Serial")
    def test_channel_range_valid(self, mock_serial_class: MagicMock) -> None:
        """Test that valid channel numbers (0-7) work."""
        mock_serial: Mock = Mock()
        mock_serial.read_all = Mock(return_value=b"OK\r\n")
        mock_serial_class.return_value = mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Valid channels (0-7) should work
        for ch in range(8):
            cd48.set_channel(ch, A=1, B=0, C=0, D=0)

    @patch("serial.Serial")
    def test_channel_range_invalid(self, mock_serial_class: MagicMock) -> None:
        """Test that invalid channel numbers raise ValueError."""
        mock_serial: Mock = Mock()
        mock_serial.read_all = Mock(return_value=b"OK\r\n")
        mock_serial_class.return_value = mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Invalid channels should raise ValueError
        with self.assertRaises(ValueError) as context:
            cd48.set_channel(8, A=1, B=0, C=0, D=0)
        self.assertIn("Channel must be 0-7", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cd48.set_channel(-1, A=1, B=0, C=0, D=0)
        self.assertIn("Channel must be 0-7", str(context.exception))

    @patch("serial.Serial")
    def test_channel_input_validation(self, mock_serial_class: MagicMock) -> None:
        """Test that invalid A, B, C, D values raise ValueError."""
        mock_serial: Mock = Mock()
        mock_serial.read_all = Mock(return_value=b"OK\r\n")
        mock_serial_class.return_value = mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Invalid A value
        with self.assertRaises(ValueError) as context:
            cd48.set_channel(0, A=2, B=0, C=0, D=0)
        self.assertIn("A must be 0 or 1", str(context.exception))

        # Invalid B value
        with self.assertRaises(ValueError) as context:
            cd48.set_channel(0, A=0, B=-1, C=0, D=0)
        self.assertIn("B must be 0 or 1", str(context.exception))


class TestCD48AdditionalMethods(unittest.TestCase):
    """Test additional CD48 methods for full coverage."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_serial: Mock = Mock(spec=serial.Serial)
        self.mock_serial.read_all = Mock(return_value=b"OK\r\n")

    @patch("serial.Serial")
    def test_get_version(self, mock_serial_class: MagicMock) -> None:
        """Test get_version command."""
        self.mock_serial.read_all.return_value = b"CD48 v1.2.3\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        result = cd48.get_version()

        self.mock_serial.write.assert_called_with(b"v\r")
        self.assertEqual(result, "CD48 v1.2.3")

    @patch("serial.Serial")
    def test_help(self, mock_serial_class: MagicMock) -> None:
        """Test help command."""
        self.mock_serial.read_all.return_value = b"Help text here\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        result = cd48.help()

        self.mock_serial.write.assert_called_with(b"H\r")
        self.assertEqual(result, "Help text here")

    @patch("serial.Serial")
    def test_test_leds(self, mock_serial_class: MagicMock) -> None:
        """Test test_leds command."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        cd48.test_leds()

        self.mock_serial.write.assert_called_with(b"T\r")

    @patch("serial.Serial")
    def test_get_overflow(self, mock_serial_class: MagicMock) -> None:
        """Test get_overflow command."""
        self.mock_serial.read_all.return_value = b"5\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        result = cd48.get_overflow()

        self.mock_serial.write.assert_called_with(b"E\r")
        self.assertEqual(result, 5)

    @patch("serial.Serial")
    def test_get_overflow_parse_error(self, mock_serial_class: MagicMock) -> None:
        """Test get_overflow raises CD48ParseError on invalid response."""
        self.mock_serial.read_all.return_value = b"invalid\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        with self.assertRaises(CD48ParseError) as context:
            cd48.get_overflow()
        self.assertIn("Failed to parse overflow response", str(context.exception))

    @patch("serial.Serial")
    def test_get_settings(self, mock_serial_class: MagicMock) -> None:
        """Test get_settings commands."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Human readable
        cd48.get_settings(human_readable=True)
        self.mock_serial.write.assert_called_with(b"P\r")

        # Machine readable
        cd48.get_settings(human_readable=False)
        self.mock_serial.write.assert_called_with(b"p\r")

    @patch("serial.Serial")
    def test_set_dac_voltage(self, mock_serial_class: MagicMock) -> None:
        """Test set_dac_voltage command."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        # Test voltage to byte conversion (2.04V -> 127)
        cd48.set_dac_voltage(2.04)
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertTrue(call_args.startswith(b"V"))
        self.assertTrue(call_args.endswith(b"\r"))

        # Test clamping high voltage
        cd48.set_dac_voltage(10.0)
        self.mock_serial.write.assert_called_with(b"V255\r")

        # Test clamping negative voltage
        cd48.set_dac_voltage(-1.0)
        self.mock_serial.write.assert_called_with(b"V0\r")

    @patch("serial.Serial")
    def test_close(self, mock_serial_class: MagicMock) -> None:
        """Test close method."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        cd48.close()

        self.mock_serial.close.assert_called_once()

    @patch("serial.Serial")
    def test_get_counts_parse_error(self, mock_serial_class: MagicMock) -> None:
        """Test get_counts raises CD48ParseError on invalid response."""
        self.mock_serial.read_all.return_value = b"invalid response\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        with self.assertRaises(CD48ParseError) as context:
            cd48.get_counts(human_readable=False)
        self.assertIn("Unexpected response format", str(context.exception))

    @patch("serial.Serial")
    def test_get_counts_value_error(self, mock_serial_class: MagicMock) -> None:
        """Test get_counts raises CD48ParseError on non-numeric values."""
        # 9 parts but non-numeric
        self.mock_serial.read_all.return_value = b"a b c d e f g h i\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        with self.assertRaises(CD48ParseError) as context:
            cd48.get_counts(human_readable=False)
        self.assertIn("Failed to parse counts response", str(context.exception))


class TestCD48Exceptions(unittest.TestCase):
    """Test exception hierarchy."""

    def test_exception_hierarchy(self) -> None:
        """Test that custom exceptions inherit from CD48Error."""
        self.assertTrue(issubclass(CD48ParseError, CD48Error))
        self.assertTrue(issubclass(CD48DeviceNotFoundError, CD48Error))
        self.assertTrue(issubclass(CD48Error, Exception))

    def test_exception_messages(self) -> None:
        """Test exception message handling."""
        parse_error = CD48ParseError("test message")
        self.assertEqual(str(parse_error), "test message")

        not_found_error = CD48DeviceNotFoundError("device not found")
        self.assertEqual(str(not_found_error), "device not found")


class TestCD48FullCoverage(unittest.TestCase):
    """Additional tests for 100% coverage."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_serial: Mock = Mock(spec=serial.Serial)
        self.mock_serial.read_all = Mock(return_value=b"OK\r\n")

    @patch("serial.Serial")
    def test_clear_counts(self, mock_serial_class: MagicMock) -> None:
        """Test clear_counts method."""
        self.mock_serial.read_all.return_value = b"100 200 300 400 50 25 10 5 0\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        cd48.clear_counts()

        # Should have sent the 'c' command
        self.mock_serial.write.assert_called_with(b"c\r")

    @patch("serial.Serial")
    def test_get_counts_human_readable(self, mock_serial_class: MagicMock) -> None:
        """Test get_counts with human_readable=True."""
        self.mock_serial.read_all.return_value = b"Formatted output\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        result = cd48.get_counts(human_readable=True)

        self.mock_serial.write.assert_called_with(b"C\r")
        self.assertEqual(result, "Formatted output")

    @patch("serial.Serial")
    def test_read_and_clear_counts_human_readable_true(self, mock_serial_class: MagicMock) -> None:
        """Test read_and_clear_counts with human_readable=True."""
        self.mock_serial.read_all.return_value = b"Formatted output\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        result = cd48.read_and_clear_counts(human_readable=True)

        self.mock_serial.write.assert_called_with(b"C\r")
        self.assertEqual(result, "Formatted output")

    @patch("serial.Serial")
    def test_read_and_clear_counts_human_readable_false(self, mock_serial_class: MagicMock) -> None:
        """Test read_and_clear_counts with human_readable=False."""
        self.mock_serial.read_all.return_value = b"100 200 300 400 50 25 10 5 0\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")
        result = cd48.read_and_clear_counts(human_readable=False)

        self.mock_serial.write.assert_called_with(b"c\r")
        assert isinstance(result, dict)
        self.assertEqual(result["counts"][0], 100)
        self.assertEqual(result["overflow"], 0)

    @patch("time.sleep")
    @patch("serial.Serial")
    def test_measure_rate(self, mock_serial_class: MagicMock, mock_sleep: MagicMock) -> None:
        """Test measure_rate method."""
        self.mock_serial.read_all.return_value = b"1000 200 300 400 50 25 10 5 0\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)
        result = cd48.measure_rate(channel=0, duration=1.0)

        self.assertEqual(result["counts"], 1000)
        self.assertEqual(result["duration"], 1.0)
        self.assertEqual(result["rate"], 1000.0)
        self.assertEqual(result["channel"], 0)

    @patch("serial.Serial")
    def test_measure_rate_invalid_channel(self, mock_serial_class: MagicMock) -> None:
        """Test measure_rate with invalid channel raises ValueError."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0")

        with self.assertRaises(ValueError) as context:
            cd48.measure_rate(channel=8, duration=1.0)
        self.assertIn("Channel must be 0-7", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cd48.measure_rate(channel=-1, duration=1.0)
        self.assertIn("Channel must be 0-7", str(context.exception))

    @patch("time.sleep")
    @patch("serial.Serial")
    def test_measure_coincidence_rate(
        self, mock_serial_class: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test measure_coincidence_rate method."""
        # First call is clear_counts, second is get_counts
        self.mock_serial.read_all.return_value = b"1000 2000 300 400 100 25 10 5 0\r\n"
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)
        result = cd48.measure_coincidence_rate(
            duration=1.0,
            singles_a_channel=0,
            singles_b_channel=1,
            coincidence_channel=4,
        )

        self.assertEqual(result["singles_a"], 1000)
        self.assertEqual(result["singles_b"], 2000)
        self.assertEqual(result["coincidences"], 100)
        self.assertEqual(result["duration"], 1.0)
        self.assertEqual(result["rate_a"], 1000.0)
        self.assertEqual(result["rate_b"], 2000.0)
        self.assertEqual(result["coincidence_rate"], 100.0)
        # Verify accidental rate calculation
        # accidental_rate = 2 * 25e-9 * 1000 * 2000 = 0.1
        self.assertAlmostEqual(result["accidental_rate"], 0.1, places=6)
        # true_coincidence_rate = 100 - 0.1 = 99.9
        self.assertAlmostEqual(result["true_coincidence_rate"], 99.9, places=4)

    @patch("serial.tools.list_ports.comports")
    @patch("serial.Serial")
    def test_init_auto_detect_cypress_vid(
        self, mock_serial_class: MagicMock, mock_comports: MagicMock
    ) -> None:
        """Test initialization with auto-detection via Cypress VID."""
        mock_port: Mock = Mock()
        mock_port.device = "/dev/ttyACM0"
        mock_port.description = "Some Device"
        mock_port.vid = 0x04B4  # Cypress VID
        mock_comports.return_value = [mock_port]

        mock_serial_class.return_value = self.mock_serial

        CD48()  # Auto-detect should find Cypress device

        # Should have connected to the Cypress device
        mock_serial_class.assert_called_with("/dev/ttyACM0", baudrate=115200, timeout=1)

    @patch("time.sleep")
    @patch("serial.Serial")
    def test_init_with_init_delay(
        self, mock_serial_class: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test initialization with custom init_delay."""
        mock_serial_class.return_value = self.mock_serial

        CD48(port="/dev/ttyUSB0", init_delay=0.5)

        # Should have slept for 0.5 seconds
        mock_sleep.assert_called()
        # Find the init delay call (first call after Serial instantiation)
        calls = mock_sleep.call_args_list
        init_delay_call = calls[0]
        self.assertEqual(init_delay_call[0][0], 0.5)

    @patch("time.sleep")
    @patch("serial.Serial")
    def test_init_with_zero_init_delay(
        self, mock_serial_class: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test initialization with init_delay=0 skips delay."""
        mock_serial_class.return_value = self.mock_serial

        CD48(port="/dev/ttyUSB0", init_delay=0)

        # With init_delay=0, the init sleep should be skipped
        # Verify that CD48 was created successfully by checking reset_input_buffer was called
        self.mock_serial.reset_input_buffer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
