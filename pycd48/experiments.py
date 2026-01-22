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
from typing import Literal, TypedDict

import numpy as np
from pydantic import BaseModel, Field, ValidationError

from .cd48 import CD48, CD48ConfigError, CoincidenceResult, RateResult


class ExperimentConfig(TypedDict, total=False):
    """Type definition for experiment configuration."""

    name: str
    description: str
    connection: dict[str, object]
    settings: dict[str, object]
    experiment: dict[str, object]
    output: dict[str, object]


class RateSummary(TypedDict):
    """Type definition for aggregated rate measurement results."""

    channel: int
    duration: float
    repeats: int
    mean_rate: float
    std_rate: float
    measurements: list[RateResult]


class CoincidenceSummary(TypedDict):
    """Type definition for aggregated coincidence measurement results."""

    duration: float
    repeats: int
    mean_true_coincidence_rate: float
    std_true_coincidence_rate: float
    measurements: list[CoincidenceResult]


class ContinuousData(TypedDict):
    """Type definition for continuous collection data."""

    timestamps: list[float]
    counts: dict[int, list[int]]
    rates: dict[int, list[float]]
    interval: float
    channels: list[int]


class VoltageSweepData(TypedDict):
    """Type definition for voltage sweep data."""

    voltages: list[float]
    counts: dict[int, list[int]]
    rates: dict[int, list[float]]
    measurement_time: float
    channels: list[int]


class ExperimentMetadata(TypedDict):
    """Type definition for experiment metadata."""

    experiment_type: str
    timestamp: float


class ExperimentResult(TypedDict, total=False):
    """Type definition for experiment results."""

    config: ExperimentConfig
    data: (
        RateResult
        | RateSummary
        | CoincidenceResult
        | CoincidenceSummary
        | ContinuousData
        | VoltageSweepData
    )
    metadata: ExperimentMetadata


# Pydantic models for validated experiment configurations


class RateExperimentModel(BaseModel):  # type: ignore[explicit-any]
    """Validated configuration for rate measurement experiments."""

    type: Literal["rate"]
    channel: int = Field(default=0, ge=0, le=7)
    duration: float = Field(default=1.0, gt=0)
    repeats: int = Field(default=1, ge=1)


class CoincidenceExperimentModel(BaseModel):  # type: ignore[explicit-any]
    """Validated configuration for coincidence measurement experiments."""

    type: Literal["coincidence"]
    duration: float = Field(default=1.0, gt=0)
    singles_a_channel: int = Field(default=0, ge=0, le=7)
    singles_b_channel: int = Field(default=1, ge=0, le=7)
    coincidence_channel: int = Field(default=4, ge=0, le=7)
    coincidence_window: float = Field(default=25e-9, gt=0)
    repeats: int = Field(default=1, ge=1)


class ContinuousExperimentModel(BaseModel):  # type: ignore[explicit-any]
    """Validated configuration for continuous collection experiments."""

    type: Literal["continuous"]
    duration: float = Field(default=60.0, gt=0)
    interval: float = Field(default=1.0, gt=0)
    channels: list[int] = Field(default=[0, 1, 4])


class VoltageSweepExperimentModel(BaseModel):  # type: ignore[explicit-any]
    """Validated configuration for voltage sweep experiments."""

    type: Literal["voltage_sweep"]
    voltage_min: float = Field(default=0.0, ge=0.0, le=4.08)
    voltage_max: float = Field(default=4.0, ge=0.0, le=4.08)
    voltage_steps: int = Field(default=20, ge=2)
    measurement_time: float = Field(default=3.0, gt=0)
    channels: list[int] = Field(default=[0, 1, 4])


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

    def _run_rate_measurement(self, cd48: CD48, experiment: dict[str, object]) -> ExperimentResult:
        """Run rate measurement experiment."""
        try:
            config = RateExperimentModel(**experiment)  # type: ignore[arg-type]
        except ValidationError as e:
            raise CD48ConfigError(f"Invalid rate experiment configuration: {e}") from e

        self._logger.info(
            f"Rate measurement: channel={config.channel}, duration={config.duration}s, "
            f"repeats={config.repeats}"
        )

        results: list[RateResult] = []
        for i in range(config.repeats):
            self._logger.info(f"Measurement {i+1}/{config.repeats}")
            result = cd48.measure_rate(channel=config.channel, duration=config.duration)
            results.append(result)
            if config.repeats > 1 and i < config.repeats - 1:
                time.sleep(0.1)  # Small delay between measurements

        # Calculate statistics if multiple measurements
        summary: RateResult | RateSummary
        if len(results) > 1:
            rates = [r["rate"] for r in results]
            summary = RateSummary(
                channel=config.channel,
                duration=config.duration,
                repeats=config.repeats,
                mean_rate=float(np.mean(rates)),
                std_rate=float(np.std(rates)),
                measurements=results,
            )
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
        self, cd48: CD48, experiment: dict[str, object]
    ) -> ExperimentResult:
        """Run coincidence measurement experiment."""
        try:
            config = CoincidenceExperimentModel(**experiment)  # type: ignore[arg-type]
        except ValidationError as e:
            raise CD48ConfigError(f"Invalid coincidence experiment configuration: {e}") from e

        self._logger.info(
            f"Coincidence measurement: duration={config.duration}s, "
            f"channels A={config.singles_a_channel}, B={config.singles_b_channel}, "
            f"AB={config.coincidence_channel}, repeats={config.repeats}"
        )

        results: list[CoincidenceResult] = []
        for i in range(config.repeats):
            self._logger.info(f"Measurement {i+1}/{config.repeats}")
            result = cd48.measure_coincidence_rate(
                duration=config.duration,
                singles_a_channel=config.singles_a_channel,
                singles_b_channel=config.singles_b_channel,
                coincidence_channel=config.coincidence_channel,
                coincidence_window=config.coincidence_window,
            )
            results.append(result)
            if config.repeats > 1 and i < config.repeats - 1:
                time.sleep(0.1)

        # Calculate statistics if multiple measurements
        summary: CoincidenceResult | CoincidenceSummary
        if len(results) > 1:
            true_rates = [r["true_coincidence_rate"] for r in results]
            summary = CoincidenceSummary(
                duration=config.duration,
                repeats=config.repeats,
                mean_true_coincidence_rate=float(np.mean(true_rates)),
                std_true_coincidence_rate=float(np.std(true_rates)),
                measurements=results,
            )
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
        self, cd48: CD48, experiment: dict[str, object]
    ) -> ExperimentResult:
        """Run continuous data collection experiment."""
        try:
            config = ContinuousExperimentModel(**experiment)  # type: ignore[arg-type]
        except ValidationError as e:
            raise CD48ConfigError(f"Invalid continuous experiment configuration: {e}") from e

        self._logger.info(
            f"Continuous collection: duration={config.duration}s, "
            f"interval={config.interval}s, channels={config.channels}"
        )

        num_measurements = int(config.duration / config.interval)
        timestamps: list[float] = []
        channel_data: dict[int, list[int]] = {ch: [] for ch in config.channels}

        start_time = time.time()

        for i in range(num_measurements):
            cd48.clear_counts()
            time.sleep(config.interval)

            data = cd48.get_counts(human_readable=False)
            elapsed = time.time() - start_time
            timestamps.append(elapsed)

            for ch in config.channels:
                if 0 <= ch < len(data["counts"]):
                    channel_data[ch].append(data["counts"][ch])

            self._logger.debug(f"Measurement {i+1}/{num_measurements}: t={elapsed:.1f}s")

        # Convert to rates (counts per second)
        rates: dict[int, list[float]] = {
            ch: [count / config.interval for count in counts] for ch, counts in channel_data.items()
        }

        continuous_data: ContinuousData = {
            "timestamps": timestamps,
            "counts": channel_data,
            "rates": rates,
            "interval": config.interval,
            "channels": config.channels,
        }

        return {
            "config": self.config,
            "data": continuous_data,
            "metadata": {
                "experiment_type": "continuous",
                "timestamp": time.time(),
            },
        }

    def _run_voltage_sweep(self, cd48: CD48, experiment: dict[str, object]) -> ExperimentResult:
        """Run voltage sweep experiment."""
        try:
            config = VoltageSweepExperimentModel(**experiment)  # type: ignore[arg-type]
        except ValidationError as e:
            raise CD48ConfigError(f"Invalid voltage sweep experiment configuration: {e}") from e

        voltages = np.linspace(config.voltage_min, config.voltage_max, config.voltage_steps)

        self._logger.info(
            f"Voltage sweep: {config.voltage_min}V to {config.voltage_max}V, "
            f"{config.voltage_steps} steps, {config.measurement_time}s per point"
        )

        voltage_data: list[float] = []
        channel_data: dict[int, list[int]] = {ch: [] for ch in config.channels}

        for i, voltage in enumerate(voltages):
            # Set DAC voltage
            cd48.set_dac_voltage(float(voltage))
            time.sleep(0.5)  # Allow equipment to settle

            # Measure
            cd48.clear_counts()
            time.sleep(config.measurement_time)
            data = cd48.get_counts(human_readable=False)

            voltage_data.append(float(voltage))
            for ch in config.channels:
                if 0 <= ch < len(data["counts"]):
                    channel_data[ch].append(data["counts"][ch])

            self._logger.debug(f"Voltage {i+1}/{config.voltage_steps}: {voltage:.2f}V")

        # Set DAC back to 0V
        cd48.set_dac_voltage(0.0)

        # Convert to rates
        rates: dict[int, list[float]] = {
            ch: [count / config.measurement_time for count in counts]
            for ch, counts in channel_data.items()
        }

        sweep_data: VoltageSweepData = {
            "voltages": voltage_data,
            "counts": channel_data,
            "rates": rates,
            "measurement_time": config.measurement_time,
            "channels": config.channels,
        }

        return {
            "config": self.config,
            "data": sweep_data,
            "metadata": {
                "experiment_type": "voltage_sweep",
                "timestamp": time.time(),
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
        directory_obj = output.get("directory", ".")
        output_dir = Path(directory_obj) if isinstance(directory_obj, str) else Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        exp_name_obj = self.config.get("name", "experiment")
        exp_name = str(exp_name_obj) if exp_name_obj is not None else "experiment"
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

        data = result.get("data")
        metadata = result.get("metadata")

        if data is None or metadata is None:
            return

        exp_type = metadata.get("experiment_type", "")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if exp_type == "continuous":
                # Continuous data format
                if isinstance(data, dict) and "timestamps" in data:
                    # Type-safe extraction with runtime checks
                    timestamps = data.get("timestamps")
                    channels = data.get("channels")
                    rates = data.get("rates")

                    if (
                        isinstance(timestamps, list)
                        and isinstance(channels, list)
                        and isinstance(rates, dict)
                    ):
                        header = ["time"] + [f"ch{ch}_rate" for ch in channels]
                        writer.writerow(header)

                        for i, x_val in enumerate(timestamps):
                            row = [x_val] + [
                                rates[ch][i] if ch in rates and i < len(rates[ch]) else 0
                                for ch in channels
                            ]
                            writer.writerow(row)

            elif exp_type == "voltage_sweep":
                # Voltage sweep data format
                if isinstance(data, dict) and "voltages" in data:
                    # Type-safe extraction with runtime checks
                    voltages = data.get("voltages")
                    channels = data.get("channels")
                    rates = data.get("rates")

                    if (
                        isinstance(voltages, list)
                        and isinstance(channels, list)
                        and isinstance(rates, dict)
                    ):
                        header = ["voltage"] + [f"ch{ch}_rate" for ch in channels]
                        writer.writerow(header)

                        for i, x_val in enumerate(voltages):
                            row = [x_val] + [
                                rates[ch][i] if ch in rates and i < len(rates[ch]) else 0
                                for ch in channels
                            ]
                            writer.writerow(row)

            else:
                # Single measurement or summary format
                if isinstance(data, dict):
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
