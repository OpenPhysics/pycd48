"""
Unit tests for YAML experiment configuration and runner.

These tests verify YAML config loading, validation, and experiment execution
without requiring actual hardware.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from pycd48 import CD48ConfigError
from pycd48.experiments import ExperimentRunner, run_experiment


class TestExperimentConfig(unittest.TestCase):
    """Test cases for YAML experiment configuration loading."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_valid_yaml(self) -> None:
        """Test loading a valid YAML configuration."""
        config_content = """
name: test_experiment
description: Test configuration

connection:
  baudrate: 115200
  timeout: 1.0

settings:
  trigger_level: 0.5
  impedance: 50ohm
  channels:
    "0": {A: 1, B: 0, C: 0, D: 0}

experiment:
  type: rate
  channel: 0
  duration: 1.0
  repeats: 1
"""
        config_path = self.temp_path / "test_config.yaml"
        config_path.write_text(config_content)

        runner = ExperimentRunner(config_path)

        self.assertEqual(runner.config["name"], "test_experiment")
        self.assertEqual(runner.config["experiment"]["type"], "rate")

    def test_missing_experiment_section(self) -> None:
        """Test validation fails when experiment section is missing."""
        config_content = """
name: test_experiment
connection:
  baudrate: 115200
"""
        config_path = self.temp_path / "invalid_config.yaml"
        config_path.write_text(config_content)

        with self.assertRaises(CD48ConfigError) as context:
            ExperimentRunner(config_path)

        self.assertIn("experiment", str(context.exception).lower())

    def test_missing_experiment_type(self) -> None:
        """Test validation fails when experiment type is missing."""
        config_content = """
name: test_experiment
experiment:
  duration: 1.0
"""
        config_path = self.temp_path / "invalid_config.yaml"
        config_path.write_text(config_content)

        with self.assertRaises(CD48ConfigError) as context:
            ExperimentRunner(config_path)

        self.assertIn("type", str(context.exception).lower())

    def test_invalid_experiment_type(self) -> None:
        """Test validation fails with invalid experiment type."""
        config_content = """
name: test_experiment
experiment:
  type: invalid_type
"""
        config_path = self.temp_path / "invalid_config.yaml"
        config_path.write_text(config_content)

        with self.assertRaises(CD48ConfigError) as context:
            ExperimentRunner(config_path)

        self.assertIn("invalid experiment type", str(context.exception).lower())

    def test_nonexistent_file(self) -> None:
        """Test loading non-existent configuration file."""
        config_path = self.temp_path / "nonexistent.yaml"

        with self.assertRaises(FileNotFoundError):
            ExperimentRunner(config_path)


class TestExperimentRunner(unittest.TestCase):
    """Test cases for experiment runner execution."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Mock serial for all tests
        self.mock_serial = Mock()
        self.mock_serial.read_all = Mock(return_value=b"100 200 300 400 50 25 10 5 0\r\n")

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    @patch("serial.Serial")
    @patch("pycd48.cd48.time.sleep")
    def test_run_rate_experiment(self, mock_sleep: MagicMock, mock_serial_class: MagicMock) -> None:
        """Test running a rate measurement experiment."""
        mock_serial_class.return_value = self.mock_serial

        config_content = """
name: test_rate
connection:
  port: /dev/ttyUSB0
settings:
  trigger_level: 0.5
  channels:
    "0": {A: 1, B: 0, C: 0, D: 0}
experiment:
  type: rate
  channel: 0
  duration: 1.0
  repeats: 1
"""
        config_path = self.temp_path / "rate_config.yaml"
        config_path.write_text(config_content)

        runner = ExperimentRunner(config_path)
        result = runner.run()

        self.assertEqual(result["metadata"]["experiment_type"], "rate")
        self.assertIn("data", result)
        self.assertIn("rate", result["data"])

    @patch("serial.Serial")
    @patch("pycd48.cd48.time.sleep")
    def test_run_coincidence_experiment(
        self, mock_sleep: MagicMock, mock_serial_class: MagicMock
    ) -> None:
        """Test running a coincidence measurement experiment."""
        mock_serial_class.return_value = self.mock_serial

        config_content = """
name: test_coincidence
connection:
  port: /dev/ttyUSB0
settings:
  trigger_level: 0.5
  channels:
    "0": {A: 1, B: 0, C: 0, D: 0}
    "1": {A: 0, B: 1, C: 0, D: 0}
    "4": {A: 1, B: 1, C: 0, D: 0}
experiment:
  type: coincidence
  duration: 1.0
  singles_a_channel: 0
  singles_b_channel: 1
  coincidence_channel: 4
  coincidence_window: 25.0e-9
  repeats: 1
"""
        config_path = self.temp_path / "coinc_config.yaml"
        config_path.write_text(config_content)

        runner = ExperimentRunner(config_path)
        result = runner.run()

        self.assertEqual(result["metadata"]["experiment_type"], "coincidence")
        self.assertIn("data", result)
        self.assertIn("coincidence_rate", result["data"])
        self.assertIn("true_coincidence_rate", result["data"])

    @patch("serial.Serial")
    @patch("pycd48.cd48.time.sleep")
    def test_run_continuous_experiment(
        self, mock_sleep: MagicMock, mock_serial_class: MagicMock
    ) -> None:
        """Test running a continuous collection experiment."""
        mock_serial_class.return_value = self.mock_serial

        config_content = """
name: test_continuous
connection:
  port: /dev/ttyUSB0
settings:
  trigger_level: 0.5
  channels:
    "0": {A: 1, B: 0, C: 0, D: 0}
experiment:
  type: continuous
  duration: 2.0
  interval: 1.0
  channels: [0]
"""
        config_path = self.temp_path / "continuous_config.yaml"
        config_path.write_text(config_content)

        runner = ExperimentRunner(config_path)
        result = runner.run()

        self.assertEqual(result["metadata"]["experiment_type"], "continuous")
        self.assertIn("data", result)
        self.assertIn("timestamps", result["data"])
        self.assertIn("rates", result["data"])

    @patch("serial.Serial")
    @patch("pycd48.cd48.time.sleep")
    def test_run_voltage_sweep_experiment(
        self, mock_sleep: MagicMock, mock_serial_class: MagicMock
    ) -> None:
        """Test running a voltage sweep experiment."""
        mock_serial_class.return_value = self.mock_serial

        config_content = """
name: test_voltage_sweep
connection:
  port: /dev/ttyUSB0
settings:
  trigger_level: 0.5
  channels:
    "0": {A: 1, B: 0, C: 0, D: 0}
experiment:
  type: voltage_sweep
  voltage_min: 0.0
  voltage_max: 2.0
  voltage_steps: 3
  measurement_time: 1.0
  channels: [0]
"""
        config_path = self.temp_path / "sweep_config.yaml"
        config_path.write_text(config_content)

        runner = ExperimentRunner(config_path)
        result = runner.run()

        self.assertEqual(result["metadata"]["experiment_type"], "voltage_sweep")
        self.assertIn("data", result)
        self.assertIn("voltages", result["data"])
        self.assertIn("rates", result["data"])


class TestExperimentOutput(unittest.TestCase):
    """Test cases for experiment output saving."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.mock_serial = Mock()
        self.mock_serial.read_all = Mock(return_value=b"100 200 300 400 50 25 10 5 0\r\n")

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    @patch("serial.Serial")
    @patch("pycd48.cd48.time.sleep")
    def test_json_output(self, mock_sleep: MagicMock, mock_serial_class: MagicMock) -> None:
        """Test JSON output file creation."""
        mock_serial_class.return_value = self.mock_serial

        output_dir = self.temp_path / "output"

        config_content = f"""
name: test_output
connection:
  port: /dev/ttyUSB0
settings:
  trigger_level: 0.5
  channels:
    "0": {{A: 1, B: 0, C: 0, D: 0}}
experiment:
  type: rate
  channel: 0
  duration: 1.0
  repeats: 1
output:
  directory: {output_dir}
  json: true
  csv: false
"""
        config_path = self.temp_path / "output_config.yaml"
        config_path.write_text(config_content)

        runner = ExperimentRunner(config_path)
        runner.run()

        # Check that output directory was created
        self.assertTrue(output_dir.exists())

        # Check that JSON file was created
        json_files = list(output_dir.glob("*.json"))
        self.assertEqual(len(json_files), 1)

        # Verify JSON content
        with open(json_files[0]) as f:
            data = json.load(f)
            self.assertIn("config", data)
            self.assertIn("data", data)
            self.assertIn("metadata", data)

    @patch("serial.Serial")
    @patch("pycd48.cd48.time.sleep")
    def test_csv_output_continuous(
        self, mock_sleep: MagicMock, mock_serial_class: MagicMock
    ) -> None:
        """Test CSV output for continuous experiment."""
        mock_serial_class.return_value = self.mock_serial

        output_dir = self.temp_path / "output"

        config_content = f"""
name: test_csv
connection:
  port: /dev/ttyUSB0
settings:
  trigger_level: 0.5
  channels:
    "0": {{A: 1, B: 0, C: 0, D: 0}}
experiment:
  type: continuous
  duration: 2.0
  interval: 1.0
  channels: [0]
output:
  directory: {output_dir}
  json: false
  csv: true
"""
        config_path = self.temp_path / "csv_config.yaml"
        config_path.write_text(config_content)

        runner = ExperimentRunner(config_path)
        runner.run()

        # Check that CSV file was created
        csv_files = list(output_dir.glob("*.csv"))
        self.assertEqual(len(csv_files), 1)

        # Verify CSV has header
        with open(csv_files[0]) as f:
            first_line = f.readline()
            self.assertIn("time", first_line.lower())


class TestRunExperimentFunction(unittest.TestCase):
    """Test cases for the run_experiment convenience function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.mock_serial = Mock()
        self.mock_serial.read_all = Mock(return_value=b"100 200 300 400 50 25 10 5 0\r\n")

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    @patch("serial.Serial")
    @patch("pycd48.cd48.time.sleep")
    def test_run_experiment_function(
        self, mock_sleep: MagicMock, mock_serial_class: MagicMock
    ) -> None:
        """Test run_experiment convenience function."""
        mock_serial_class.return_value = self.mock_serial

        config_content = """
name: test_function
connection:
  port: /dev/ttyUSB0
settings:
  trigger_level: 0.5
  channels:
    "0": {A: 1, B: 0, C: 0, D: 0}
experiment:
  type: rate
  channel: 0
  duration: 1.0
  repeats: 1
"""
        config_path = self.temp_path / "function_config.yaml"
        config_path.write_text(config_content)

        result = run_experiment(config_path)

        self.assertIn("data", result)
        self.assertIn("metadata", result)
        self.assertEqual(result["metadata"]["experiment_type"], "rate")


if __name__ == "__main__":
    unittest.main()
