"""
Experiment Configuration and Runner

This module provides YAML-based configuration for CD48 experiments,
enabling better reproducibility and easier collaboration.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, TypedDict

import numpy as np

from .cd48 import CD48, CD48ConfigError


class ExperimentConfig(TypedDict, total=False):
    """Type definition for experiment configuration."""

    name: str
    description: str
    connection: dict[str, Any]
    settings: dict[str, Any]
    experiment: dict[str, Any]
    output: dict[str, Any]


class ExperimentResult(TypedDict, total=False):
    """Type definition for experiment results."""

    config: ExperimentConfig
    data: dict[str, Any]
    metadata: dict[str, Any]


class ExperimentRunner:
    """Run experiments from YAML configuration files."""

    def __init__(self, config_path: str | Path) -> None:
        """
        Initialize experiment runner with configuration file.

        Parameters:
        -----------
        config_path : str or Path
            Path to YAML configuration file

        Raises:
        -------
        CD48ConfigError
            If configuration file is invalid
        FileNotFoundError
            If configuration file does not exist
        """
        self.config_path = Path(config_path)
        self._logger = logging.getLogger(__name__)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Load configuration
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> ExperimentConfig:
        """Load experiment configuration from YAML file."""
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as e:
            raise CD48ConfigError(
                "PyYAML is required for experiment configs. Install with: pip install pyyaml"
            ) from e

        with open(self.config_path, encoding="utf-8") as f:
            try:
                config: ExperimentConfig = yaml.safe_load(f)
                return config if config is not None else {}
            except yaml.YAMLError as e:
                raise CD48ConfigError(f"Invalid YAML in config file: {e}") from e

    def _validate_config(self) -> None:
        """Validate experiment configuration."""
        if "experiment" not in self.config:
            raise CD48ConfigError("Configuration must include 'experiment' section")

        experiment = self.config["experiment"]
        if not isinstance(experiment, dict):
            raise CD48ConfigError("'experiment' section must be a dictionary")

        if "type" not in experiment:
            raise CD48ConfigError("Experiment must specify 'type'")

        valid_types = ["rate", "coincidence", "continuous", "voltage_sweep"]
        exp_type = experiment["type"]
        if exp_type not in valid_types:
            raise CD48ConfigError(
                f"Invalid experiment type '{exp_type}'. Must be one of: {valid_types}"
            )

    def run(self) -> ExperimentResult:
        """
        Run the configured experiment.

        Returns:
        --------
        ExperimentResult : Experiment results including data and metadata

        Raises:
        -------
        CD48ConfigError
            If experiment configuration is invalid
        """
        self._logger.info(f"Running experiment from {self.config_path}")

        # Create CD48 instance from config
        cd48 = CD48.from_config(self.config_path, apply_settings=True)

        try:
            # Get experiment type and run appropriate handler
            exp_type = self.config["experiment"]["type"]
            experiment = self.config["experiment"]

            if exp_type == "rate":
                result = self._run_rate_measurement(cd48, experiment)
            elif exp_type == "coincidence":
                result = self._run_coincidence_measurement(cd48, experiment)
            elif exp_type == "continuous":
                result = self._run_continuous_collection(cd48, experiment)
            elif exp_type == "voltage_sweep":
                result = self._run_voltage_sweep(cd48, experiment)
            else:
                raise CD48ConfigError(f"Unsupported experiment type: {exp_type}")

            # Save results if output is configured
            self._save_results(result)

            return result

        finally:
            cd48.close()

    def _run_rate_measurement(self, cd48: CD48, experiment: dict[str, Any]) -> ExperimentResult:
        """Run rate measurement experiment."""
        channel = experiment.get("channel", 0)
        duration = experiment.get("duration", 1.0)
        repeats = experiment.get("repeats", 1)

        self._logger.info(
            f"Rate measurement: channel={channel}, duration={duration}s, repeats={repeats}"
        )

        results = []
        for i in range(repeats):
            self._logger.info(f"Measurement {i+1}/{repeats}")
            result = cd48.measure_rate(channel=channel, duration=duration)
            results.append(result)
            if repeats > 1 and i < repeats - 1:
                time.sleep(0.1)  # Small delay between measurements

        # Calculate statistics if multiple measurements
        summary: Any
        if len(results) > 1:
            rates = [r["rate"] for r in results]
            summary = {
                "channel": channel,
                "duration": duration,
                "repeats": repeats,
                "mean_rate": float(np.mean(rates)),
                "std_rate": float(np.std(rates)),
                "measurements": results,
            }
        else:
            summary = results[0]

        return {
            "config": self.config,
            "data": summary,
            "metadata": {
                "experiment_type": "rate",
                "timestamp": time.time(),
            },
        }

    def _run_coincidence_measurement(
        self, cd48: CD48, experiment: dict[str, Any]
    ) -> ExperimentResult:
        """Run coincidence measurement experiment."""
        duration = experiment.get("duration", 1.0)
        singles_a = experiment.get("singles_a_channel", 0)
        singles_b = experiment.get("singles_b_channel", 1)
        coincidence = experiment.get("coincidence_channel", 4)
        window = experiment.get("coincidence_window", 25e-9)
        repeats = experiment.get("repeats", 1)

        self._logger.info(
            f"Coincidence measurement: duration={duration}s, "
            f"channels A={singles_a}, B={singles_b}, AB={coincidence}, repeats={repeats}"
        )

        results = []
        for i in range(repeats):
            self._logger.info(f"Measurement {i+1}/{repeats}")
            result = cd48.measure_coincidence_rate(
                duration=duration,
                singles_a_channel=singles_a,
                singles_b_channel=singles_b,
                coincidence_channel=coincidence,
                coincidence_window=window,
            )
            results.append(result)
            if repeats > 1 and i < repeats - 1:
                time.sleep(0.1)

        # Calculate statistics if multiple measurements
        summary: Any
        if len(results) > 1:
            true_rates = [r["true_coincidence_rate"] for r in results]
            summary = {
                "duration": duration,
                "repeats": repeats,
                "mean_true_coincidence_rate": float(np.mean(true_rates)),
                "std_true_coincidence_rate": float(np.std(true_rates)),
                "measurements": results,
            }
        else:
            summary = results[0]

        return {
            "config": self.config,
            "data": summary,
            "metadata": {
                "experiment_type": "coincidence",
                "timestamp": time.time(),
            },
        }

    def _run_continuous_collection(
        self, cd48: CD48, experiment: dict[str, Any]
    ) -> ExperimentResult:
        """Run continuous data collection experiment."""
        duration = experiment.get("duration", 60.0)
        interval = experiment.get("interval", 1.0)
        channels = experiment.get("channels", [0, 1, 4])

        self._logger.info(
            f"Continuous collection: duration={duration}s, "
            f"interval={interval}s, channels={channels}"
        )

        num_measurements = int(duration / interval)
        timestamps = []
        channel_data: dict[int, list[int]] = {ch: [] for ch in channels}

        start_time = time.time()

        for i in range(num_measurements):
            cd48.clear_counts()
            time.sleep(interval)

            data = cd48.get_counts(human_readable=False)
            elapsed = time.time() - start_time
            timestamps.append(elapsed)

            for ch in channels:
                if 0 <= ch < len(data["counts"]):
                    channel_data[ch].append(data["counts"][ch])

            self._logger.debug(f"Measurement {i+1}/{num_measurements}: t={elapsed:.1f}s")

        # Convert to rates (counts per second)
        rates = {ch: [count / interval for count in counts] for ch, counts in channel_data.items()}

        return {
            "config": self.config,
            "data": {
                "timestamps": timestamps,
                "counts": channel_data,
                "rates": rates,
                "interval": interval,
                "channels": channels,
            },
            "metadata": {
                "experiment_type": "continuous",
                "timestamp": time.time(),
                "duration": duration,
                "num_measurements": num_measurements,
            },
        }

    def _run_voltage_sweep(self, cd48: CD48, experiment: dict[str, Any]) -> ExperimentResult:
        """Run voltage sweep experiment."""
        v_min = experiment.get("voltage_min", 0.0)
        v_max = experiment.get("voltage_max", 4.0)
        v_steps = experiment.get("voltage_steps", 20)
        measurement_time = experiment.get("measurement_time", 3.0)
        channels = experiment.get("channels", [0, 1, 4])

        voltages = np.linspace(v_min, v_max, v_steps)

        self._logger.info(
            f"Voltage sweep: {v_min}V to {v_max}V, "
            f"{v_steps} steps, {measurement_time}s per point"
        )

        voltage_data = []
        channel_data: dict[int, list[int]] = {ch: [] for ch in channels}

        for i, voltage in enumerate(voltages):
            # Set DAC voltage
            cd48.set_dac_voltage(float(voltage))
            time.sleep(0.5)  # Allow equipment to settle

            # Measure
            cd48.clear_counts()
            time.sleep(measurement_time)
            data = cd48.get_counts(human_readable=False)

            voltage_data.append(float(voltage))
            for ch in channels:
                if 0 <= ch < len(data["counts"]):
                    channel_data[ch].append(data["counts"][ch])

            self._logger.debug(f"Voltage {i+1}/{v_steps}: {voltage:.2f}V")

        # Set DAC back to 0V
        cd48.set_dac_voltage(0.0)

        # Convert to rates
        rates = {
            ch: [count / measurement_time for count in counts]
            for ch, counts in channel_data.items()
        }

        return {
            "config": self.config,
            "data": {
                "voltages": voltage_data,
                "counts": channel_data,
                "rates": rates,
                "measurement_time": measurement_time,
                "channels": channels,
            },
            "metadata": {
                "experiment_type": "voltage_sweep",
                "timestamp": time.time(),
                "voltage_range": [v_min, v_max],
                "num_points": v_steps,
            },
        }

    def _save_results(self, result: ExperimentResult) -> None:
        """Save experiment results to file."""
        if "output" not in self.config:
            return

        output = self.config["output"]
        if not isinstance(output, dict):
            return

        # Create output directory if specified
        output_dir = Path(output.get("directory", "."))
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        exp_name = self.config.get("name", "experiment")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_name = f"{exp_name}_{timestamp}"

        # Save JSON
        if output.get("json", False):
            json_path = output_dir / f"{base_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)
            self._logger.info(f"Results saved to {json_path}")

        # Save CSV
        if output.get("csv", False):
            csv_path = output_dir / f"{base_name}.csv"
            self._save_csv(result, csv_path)
            self._logger.info(f"Results saved to {csv_path}")

    def _save_csv(self, result: ExperimentResult, path: Path) -> None:
        """Save experiment results to CSV file."""
        import csv

        data = result.get("data", {})
        exp_type = result.get("metadata", {}).get("experiment_type", "")

        with open(path, "w", newline="", encoding="utf-8") as f:
            if exp_type == "continuous" or exp_type == "voltage_sweep":
                # Time series or sweep data
                if exp_type == "continuous":
                    x_key = "timestamps"
                    x_label = "time"
                else:
                    x_key = "voltages"
                    x_label = "voltage"

                x_data = data.get(x_key, [])
                channels = data.get("channels", [])
                rates = data.get("rates", {})

                writer = csv.writer(f)
                header = [x_label] + [f"ch{ch}_rate" for ch in channels]
                writer.writerow(header)

                for i, x_val in enumerate(x_data):
                    row = [x_val] + [rates[ch][i] if ch in rates else 0 for ch in channels]
                    writer.writerow(row)

            else:
                # Single measurement or summary
                writer = csv.writer(f)
                for key, value in data.items():
                    if not isinstance(value, (list, dict)):
                        writer.writerow([key, value])


def run_experiment(config_path: str | Path) -> ExperimentResult:
    """
    Run an experiment from a YAML configuration file.

    This is a convenience function that creates an ExperimentRunner
    and runs the experiment.

    Parameters:
    -----------
    config_path : str or Path
        Path to YAML experiment configuration file

    Returns:
    --------
    ExperimentResult : Experiment results

    Example:
    --------
    >>> result = run_experiment("configs/cosmic_ray.yaml")
    >>> print(f"Mean rate: {result['data']['mean_rate']:.2f} Hz")
    """
    runner = ExperimentRunner(config_path)
    return runner.run()
