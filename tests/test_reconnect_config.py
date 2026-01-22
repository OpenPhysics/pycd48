"""
Unit tests for CD48 reconnection and configuration features.

These tests cover:
- CD48.from_config() for loading configuration from files
- CD48.reconnect() for manual reconnection
- CD48WithReconnect for automatic reconnection
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import serial

from pycd48 import (
    CD48,
    CD48ConfigError,
    CD48ConnectionError,
    CD48WithReconnect,
)


class TestCD48FromConfig(unittest.TestCase):
    """Test cases for CD48.from_config() method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_serial: Mock = Mock(spec=serial.Serial)
        self.mock_serial.read_all = Mock(return_value=b"OK\r\n")
        self.mock_serial.is_open = True

    def _create_config_file(self, config: dict[str, object], suffix: str = ".json") -> Path:
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            if suffix == ".json":
                json.dump(config, f)
            else:
                # YAML format
                import yaml

                yaml.dump(config, f)
            return Path(f.name)

    @patch("serial.Serial")
    def test_from_config_json_basic(self, mock_serial_class: MagicMock) -> None:
        """Test loading basic configuration from JSON file."""
        mock_serial_class.return_value = self.mock_serial

        config = {
            "connection": {
                "port": "/dev/ttyUSB0",
                "baudrate": 115200,
                "timeout": 1.0,
                "init_delay": 0,
            }
        }
        config_path = self._create_config_file(config)

        try:
            cd48 = CD48.from_config(config_path)
            mock_serial_class.assert_called_once_with("/dev/ttyUSB0", baudrate=115200, timeout=1.0)
            self.assertIsNotNone(cd48.ser)
        finally:
            config_path.unlink()

    @patch("serial.Serial")
    def test_from_config_with_settings(self, mock_serial_class: MagicMock) -> None:
        """Test loading configuration with device settings."""
        mock_serial_class.return_value = self.mock_serial

        config = {
            "connection": {"port": "/dev/ttyUSB0", "init_delay": 0},
            "settings": {
                "trigger_level": 1.5,
                "impedance": "50ohm",
                "dac_voltage": 2.0,
                "channels": {
                    "0": {"A": 1, "B": 0, "C": 0, "D": 0},
                    "4": {"A": 1, "B": 1, "C": 0, "D": 0},
                },
            },
        }
        config_path = self._create_config_file(config)

        try:
            CD48.from_config(config_path)

            # Verify settings were applied (check write calls)
            write_calls = [call[0][0] for call in self.mock_serial.write.call_args_list]

            # Should have trigger level, impedance, DAC, and channel commands
            self.assertTrue(any(b"L" in call for call in write_calls))  # Trigger
            self.assertTrue(any(b"z" in call for call in write_calls))  # 50ohm
            self.assertTrue(any(b"V" in call for call in write_calls))  # DAC
            self.assertTrue(any(b"S01000" in call for call in write_calls))  # Channel 0
            self.assertTrue(any(b"S41100" in call for call in write_calls))  # Channel 4
        finally:
            config_path.unlink()

    @patch("serial.Serial")
    def test_from_config_skip_settings(self, mock_serial_class: MagicMock) -> None:
        """Test loading configuration without applying settings."""
        mock_serial_class.return_value = self.mock_serial

        config = {
            "connection": {"port": "/dev/ttyUSB0", "init_delay": 0},
            "settings": {"trigger_level": 1.5},
        }
        config_path = self._create_config_file(config)

        try:
            CD48.from_config(config_path, apply_settings=False)

            # No settings commands should be sent (only init reset)
            write_calls = self.mock_serial.write.call_args_list
            self.assertEqual(len(write_calls), 0)
        finally:
            config_path.unlink()

    def test_from_config_file_not_found(self) -> None:
        """Test error when config file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            CD48.from_config("/nonexistent/config.json")

    def test_from_config_invalid_json(self) -> None:
        """Test error on invalid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("{ invalid json }")
            config_path = Path(f.name)

        try:
            with self.assertRaises(CD48ConfigError) as context:
                CD48.from_config(config_path)
            self.assertIn("Invalid JSON", str(context.exception))
        finally:
            config_path.unlink()

    def test_from_config_unsupported_format(self) -> None:
        """Test error on unsupported file format."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("some text")
            config_path = Path(f.name)

        try:
            with self.assertRaises(CD48ConfigError) as context:
                CD48.from_config(config_path)
            self.assertIn("Unsupported config file format", str(context.exception))
        finally:
            config_path.unlink()

    @patch("serial.Serial")
    def test_from_config_yaml(self, mock_serial_class: MagicMock) -> None:
        """Test loading configuration from YAML file."""
        mock_serial_class.return_value = self.mock_serial

        import importlib.util

        if importlib.util.find_spec("yaml") is None:
            self.skipTest("PyYAML not installed")

        config = {
            "connection": {"port": "/dev/ttyUSB0", "init_delay": 0},
            "settings": {"trigger_level": 2.0},
        }
        config_path = self._create_config_file(config, suffix=".yaml")

        try:
            cd48 = CD48.from_config(config_path)
            self.assertIsNotNone(cd48.ser)
        finally:
            config_path.unlink()

    @patch("serial.Serial")
    def test_from_config_highz_impedance(self, mock_serial_class: MagicMock) -> None:
        """Test configuration with high-Z impedance."""
        mock_serial_class.return_value = self.mock_serial

        config = {
            "connection": {"port": "/dev/ttyUSB0", "init_delay": 0},
            "settings": {"impedance": "highz"},
        }
        config_path = self._create_config_file(config)

        try:
            CD48.from_config(config_path)
            write_calls = [call[0][0] for call in self.mock_serial.write.call_args_list]
            self.assertTrue(any(b"Z" in call for call in write_calls))
        finally:
            config_path.unlink()


class TestCD48Reconnect(unittest.TestCase):
    """Test cases for CD48.reconnect() method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_serial: Mock = Mock(spec=serial.Serial)
        self.mock_serial.read_all = Mock(return_value=b"OK\r\n")
        self.mock_serial.is_open = True

    @patch("serial.Serial")
    def test_reconnect_success(self, mock_serial_class: MagicMock) -> None:
        """Test successful reconnection."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)
        self.assertTrue(cd48.is_connected)

        # Simulate disconnect and reconnect
        cd48.reconnect()

        # Should have called Serial twice (initial + reconnect)
        self.assertEqual(mock_serial_class.call_count, 2)

    @patch("serial.Serial")
    def test_reconnect_closes_existing(self, mock_serial_class: MagicMock) -> None:
        """Test that reconnect closes existing connection."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)
        cd48.reconnect()

        # Should have closed the first connection
        self.mock_serial.close.assert_called()

    @patch("serial.Serial")
    def test_reconnect_with_delay(self, mock_serial_class: MagicMock) -> None:
        """Test reconnection with custom init delay."""
        mock_serial_class.return_value = self.mock_serial

        with patch("time.sleep") as mock_sleep:
            cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)
            cd48.reconnect(init_delay=0.5)

            # Should have slept for 0.5 seconds during reconnect
            mock_sleep.assert_called_with(0.5)

    @patch("serial.Serial")
    def test_reconnect_failure(self, mock_serial_class: MagicMock) -> None:
        """Test reconnection failure."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)

        # Make subsequent Serial() calls fail
        mock_serial_class.side_effect = serial.SerialException("Port not available")

        with self.assertRaises(CD48ConnectionError):
            cd48.reconnect()

    @patch("serial.Serial")
    def test_is_connected_property(self, mock_serial_class: MagicMock) -> None:
        """Test is_connected property."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)
        self.assertTrue(cd48.is_connected)

        self.mock_serial.is_open = False
        self.assertFalse(cd48.is_connected)

    @patch("serial.Serial")
    def test_port_property(self, mock_serial_class: MagicMock) -> None:
        """Test port property."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48(port="/dev/ttyUSB0", init_delay=0)
        self.assertEqual(cd48.port, "/dev/ttyUSB0")


class TestCD48WithReconnect(unittest.TestCase):
    """Test cases for CD48WithReconnect class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_serial: Mock = Mock(spec=serial.Serial)
        self.mock_serial.read_all = Mock(return_value=b"OK\r\n")
        self.mock_serial.is_open = True

    @patch("serial.Serial")
    def test_auto_reconnect_on_failure(self, mock_serial_class: MagicMock) -> None:
        """Test automatic reconnection on command failure."""
        mock_serial_class.return_value = self.mock_serial

        call_count = 0

        def failing_then_success(*args: object) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise serial.SerialException("Connection lost")
            return b"OK\r\n"

        self.mock_serial.write.side_effect = failing_then_success

        reconnect_called = False

        def on_reconnect() -> None:
            nonlocal reconnect_called
            reconnect_called = True

        with patch("time.sleep"):
            cd48 = CD48WithReconnect(
                port="/dev/ttyUSB0",
                init_delay=0,
                on_reconnect=on_reconnect,
            )

            # This should trigger reconnection
            cd48._send_command("C")

            self.assertTrue(reconnect_called)

    @patch("serial.Serial")
    def test_disconnect_callback(self, mock_serial_class: MagicMock) -> None:
        """Test disconnect callback is called."""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.write.side_effect = serial.SerialException("Connection lost")

        disconnect_called = False

        def on_disconnect() -> None:
            nonlocal disconnect_called
            disconnect_called = True

        with patch("time.sleep"):
            cd48 = CD48WithReconnect(
                port="/dev/ttyUSB0",
                init_delay=0,
                on_disconnect=on_disconnect,
                max_reconnect_attempts=1,
            )

            with self.assertRaises(CD48ConnectionError):
                cd48._send_command("C")

            self.assertTrue(disconnect_called)

    @patch("serial.Serial")
    def test_try_reconnect_success(self, mock_serial_class: MagicMock) -> None:
        """Test try_reconnect method succeeds."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48WithReconnect(port="/dev/ttyUSB0", init_delay=0)

        result = cd48.try_reconnect()
        self.assertTrue(result)

    @patch("serial.Serial")
    def test_try_reconnect_max_attempts(self, mock_serial_class: MagicMock) -> None:
        """Test try_reconnect respects max attempts."""
        mock_serial_class.return_value = self.mock_serial

        cd48 = CD48WithReconnect(
            port="/dev/ttyUSB0",
            init_delay=0,
            max_reconnect_attempts=3,
        )

        # Make all reconnection attempts fail
        mock_serial_class.side_effect = serial.SerialException("Port not available")

        with patch("time.sleep"):
            result = cd48.try_reconnect()

        self.assertFalse(result)
        # Should have attempted 3 times (initial + max_attempts calls)
        # First call is in __init__, then 3 attempts in try_reconnect
        self.assertEqual(mock_serial_class.call_count, 4)

    @patch("serial.Serial")
    def test_auto_reconnect_disabled(self, mock_serial_class: MagicMock) -> None:
        """Test behavior when auto_reconnect is disabled."""
        mock_serial_class.return_value = self.mock_serial
        self.mock_serial.write.side_effect = serial.SerialException("Connection lost")

        cd48 = CD48WithReconnect(
            port="/dev/ttyUSB0",
            init_delay=0,
            auto_reconnect=False,
        )

        with self.assertRaises(CD48ConnectionError):
            cd48._send_command("C")

        # Should only have initial Serial() call, no reconnection attempts
        self.assertEqual(mock_serial_class.call_count, 1)

    @patch("serial.Serial")
    def test_context_manager(self, mock_serial_class: MagicMock) -> None:
        """Test context manager support."""
        mock_serial_class.return_value = self.mock_serial

        with CD48WithReconnect(port="/dev/ttyUSB0", init_delay=0) as cd48:
            self.assertIsNotNone(cd48.ser)

        self.mock_serial.close.assert_called_once()


class TestCD48Exceptions(unittest.TestCase):
    """Test new exception classes."""

    def test_connection_error(self) -> None:
        """Test CD48ConnectionError."""
        error = CD48ConnectionError("Connection lost")
        self.assertEqual(str(error), "Connection lost")
        self.assertIsInstance(error, Exception)

    def test_config_error(self) -> None:
        """Test CD48ConfigError."""
        error = CD48ConfigError("Invalid config")
        self.assertEqual(str(error), "Invalid config")
        self.assertIsInstance(error, Exception)


if __name__ == "__main__":
    unittest.main()
