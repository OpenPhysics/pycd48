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
from typing import Annotated, Literal, Self

import numpy as np
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    model_validator,
)

from .cd48 import CD48
from .config import CD48ConfigError
from .protocols import CoincidenceResult, RateResult

# =============================================================================
# Custom Types with Validation
# =============================================================================


def _validate_channel(v: int) -> int:
    """Validate that channel is in valid range 0-7."""
    if not 0 <= v <= 7:
        raise ValueError(f"Channel must be 0-7, got {v}")
    return v


def _validate_channels_list(v: list[int]) -> list[int]:
    """Validate that all channels in list are in valid range 0-7."""
    for ch in v:
        if not 0 <= ch <= 7:
            raise ValueError(f"Channel must be 0-7, got {ch}")
    return v


# Reusable validated types
Channel = Annotated[int, AfterValidator(_validate_channel)]
ChannelList = Annotated[list[int], AfterValidator(_validate_channels_list)]


# =============================================================================
# Experiment Configuration Models (Discriminated Union)
# =============================================================================


class RateExperimentModel(BaseModel):
    """Validated configuration for rate measurement experiments."""

    model_config = ConfigDict(strict=True)

    type: Literal["rate"]
    channel: Channel = 0
    duration: float = Field(default=1.0, gt=0)
    repeats: int = Field(default=1, ge=1)


class CoincidenceExperimentModel(BaseModel):
    """Validated configuration for coincidence measurement experiments."""

    model_config = ConfigDict(strict=True)

    type: Literal["coincidence"]
    duration: float = Field(default=1.0, gt=0)
    singles_a_channel: Channel = 0
    singles_b_channel: Channel = 1
    coincidence_channel: Channel = 4
    coincidence_window: float = Field(default=25e-9, gt=0)
    repeats: int = Field(default=1, ge=1)


class ContinuousExperimentModel(BaseModel):
    """Validated configuration for continuous collection experiments."""

    model_config = ConfigDict(strict=True)

    type: Literal["continuous"]
    duration: float = Field(default=60.0, gt=0)
    interval: float = Field(default=1.0, gt=0)
    channels: ChannelList = Field(default=[0, 1, 4])


class VoltageSweepExperimentModel(BaseModel):
    """Validated configuration for voltage sweep experiments."""

    model_config = ConfigDict(strict=True)

    type: Literal["voltage_sweep"]
    voltage_min: float = Field(default=0.0, ge=0.0, le=4.08)
    voltage_max: float = Field(default=4.0, ge=0.0, le=4.08)
    voltage_steps: int = Field(default=20, ge=2)
    measurement_time: float = Field(default=3.0, gt=0)
    channels: ChannelList = Field(default=[0, 1, 4])

    @model_validator(mode="after")
    def check_voltage_range(self) -> Self:
        """Ensure voltage_min is less than voltage_max."""
        if self.voltage_min >= self.voltage_max:
            raise ValueError(
                f"voltage_min ({self.voltage_min}) must be less than "
                f"voltage_max ({self.voltage_max})"
            )
        return self


# Discriminated union - Pydantic auto-dispatches based on 'type' field
ExperimentModel = Annotated[
    RateExperimentModel
    | CoincidenceExperimentModel
    | ContinuousExperimentModel
    | VoltageSweepExperimentModel,
    Discriminator("type"),
]


# =============================================================================
# Configuration Section Models
# =============================================================================


class ChannelConfig(BaseModel):
    """Configuration for a single channel's input selection."""

    model_config = ConfigDict(strict=True)

    A: int = Field(default=0, ge=0, le=1)
    B: int = Field(default=0, ge=0, le=1)
    C: int = Field(default=0, ge=0, le=1)
    D: int = Field(default=0, ge=0, le=1)


class ConnectionConfig(BaseModel):
    """Device connection configuration."""

    model_config = ConfigDict(extra="allow")  # Allow extra fields like 'port'

    port: str | None = None
    baudrate: int = 115200
    timeout: float = 1.0
    init_delay: float = 2.0


class SettingsConfig(BaseModel):
    """Device settings configuration."""

    model_config = ConfigDict(extra="allow")  # Allow extra fields

    trigger_level: float | None = None
    impedance: Literal["50ohm", "1Mohm"] | None = None
    channels: dict[str, ChannelConfig] | None = None


class OutputConfig(BaseModel):
    """Output configuration for experiment results."""

    model_config = ConfigDict(populate_by_name=True)  # Allow string->Path coercion

    directory: Path = Path(".")
    save_json: bool = Field(default=False, alias="json")
    save_csv: bool = Field(default=False, alias="csv")


class FullExperimentConfig(BaseModel):
    """
    Complete experiment configuration with full validation.

    This model validates the entire YAML configuration file structure.
    """

    model_config = ConfigDict(extra="allow")  # Allow extra fields for extensibility

    name: str = "experiment"
    description: str = ""
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    settings: SettingsConfig = Field(default_factory=SettingsConfig)
    experiment: ExperimentModel  # Required - discriminated union
    output: OutputConfig = Field(default_factory=OutputConfig)


# =============================================================================
# Result Models
# =============================================================================


class RateMeasurementModel(BaseModel):
    """Single rate measurement result (Pydantic equivalent of RateResult TypedDict)."""

    counts: int
    duration: float
    rate: float
    channel: int


class CoincidenceMeasurementModel(BaseModel):
    """Single coincidence measurement result (Pydantic equivalent of CoincidenceResult)."""

    singles_a: int
    singles_b: int
    coincidences: int
    duration: float
    rate_a: float
    rate_b: float
    coincidence_rate: float
    accidental_rate: float
    true_coincidence_rate: float


class RateSummaryModel(BaseModel):
    """Aggregated rate measurement results."""

    channel: int
    duration: float
    repeats: int
    mean_rate: float
    std_rate: float
    measurements: list[RateMeasurementModel]


class CoincidenceSummaryModel(BaseModel):
    """Aggregated coincidence measurement results."""

    duration: float
    repeats: int
    mean_true_coincidence_rate: float
    std_true_coincidence_rate: float
    measurements: list[CoincidenceMeasurementModel]


class ContinuousDataModel(BaseModel):
    """Continuous collection data."""

    timestamps: list[float]
    counts: dict[int, list[int]]
    rates: dict[int, list[float]]
    interval: float
    channels: list[int]


class VoltageSweepDataModel(BaseModel):
    """Voltage sweep data."""

    voltages: list[float]
    counts: dict[int, list[int]]
    rates: dict[int, list[float]]
    measurement_time: float
    channels: list[int]


class ExperimentMetadataModel(BaseModel):
    """Experiment metadata."""

    experiment_type: str
    timestamp: float


# Union type for all possible experiment data results
ExperimentData = (
    RateMeasurementModel
    | RateSummaryModel
    | CoincidenceMeasurementModel
    | CoincidenceSummaryModel
    | ContinuousDataModel
    | VoltageSweepDataModel
)


class ExperimentResultModel(BaseModel):
    """Complete experiment result with config, data, and metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: FullExperimentConfig
    data: ExperimentData
    metadata: ExperimentMetadataModel


# Type alias for backward compatibility - dict representation
ExperimentResult = dict[str, object]


# =============================================================================
# Experiment Runner
# =============================================================================


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

        # Load and validate configuration using Pydantic
        self._config_model = self._load_and_validate_config()

        # Expose config as dict for backward compatibility
        self.config = self._config_model.model_dump(mode="python")

    def _load_and_validate_config(self) -> FullExperimentConfig:
        """Load and validate experiment configuration from YAML file."""
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as e:
            raise CD48ConfigError(
                "PyYAML is required for experiment configs. Install with: pip install pyyaml"
            ) from e

        with open(self.config_path, encoding="utf-8") as f:
            try:
                raw_config = yaml.safe_load(f)
                if raw_config is None:
                    raw_config = {}
            except yaml.YAMLError as e:
                raise CD48ConfigError(f"Invalid YAML in config file: {e}") from e

        # Validate required experiment section before Pydantic validation
        if "experiment" not in raw_config:
            raise CD48ConfigError("Configuration must include 'experiment' section")

        experiment = raw_config.get("experiment", {})
        if not isinstance(experiment, dict):
            raise CD48ConfigError("'experiment' section must be a dictionary")

        if "type" not in experiment:
            raise CD48ConfigError("Experiment must specify 'type'")

        valid_types = ["rate", "coincidence", "continuous", "voltage_sweep"]
        exp_type = experiment.get("type")
        if exp_type not in valid_types:
            raise CD48ConfigError(
                f"Invalid experiment type '{exp_type}'. Must be one of: {valid_types}"
            )

        # Use Pydantic for full validation
        try:
            config: FullExperimentConfig = FullExperimentConfig.model_validate(raw_config)
            return config
        except Exception as e:
            raise CD48ConfigError(f"Invalid configuration: {e}") from e

    def run(self) -> ExperimentResult:
        """
        Run the configured experiment.

        Returns:
        --------
        ExperimentResult : Experiment results as dict (for backward compatibility)

        Raises:
        -------
        CD48ConfigError
            If experiment configuration is invalid
        """
        self._logger.info(f"Running experiment from {self.config_path}")

        # Create CD48 instance from config
        cd48 = CD48.from_config(self.config_path, apply_settings_flag=True)

        try:
            # Get experiment model - already validated
            experiment = self._config_model.experiment

            # Dispatch based on experiment type using pattern matching
            match experiment:
                case RateExperimentModel():
                    result_model = self._run_rate_measurement(cd48, experiment)
                case CoincidenceExperimentModel():
                    result_model = self._run_coincidence_measurement(cd48, experiment)
                case ContinuousExperimentModel():
                    result_model = self._run_continuous_collection(cd48, experiment)
                case VoltageSweepExperimentModel():
                    result_model = self._run_voltage_sweep(cd48, experiment)

            # Save results if output is configured
            self._save_results(result_model)

            # Return as dict for backward compatibility
            result: ExperimentResult = result_model.model_dump(mode="python")
            return result

        finally:
            cd48.close()

    def _run_rate_measurement(
        self, cd48: CD48, config: RateExperimentModel
    ) -> ExperimentResultModel:
        """Run rate measurement experiment."""
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
        data: RateMeasurementModel | RateSummaryModel
        if len(results) > 1:
            rates = [r["rate"] for r in results]
            # Convert TypedDict results to Pydantic models
            measurements = [RateMeasurementModel.model_validate(r) for r in results]
            data = RateSummaryModel(
                channel=config.channel,
                duration=config.duration,
                repeats=config.repeats,
                mean_rate=float(np.mean(rates)),
                std_rate=float(np.std(rates)),
                measurements=measurements,
            )
        else:
            data = RateMeasurementModel.model_validate(results[0])

        return ExperimentResultModel(
            config=self._config_model,
            data=data,
            metadata=ExperimentMetadataModel(
                experiment_type="rate",
                timestamp=time.time(),
            ),
        )

    def _run_coincidence_measurement(
        self, cd48: CD48, config: CoincidenceExperimentModel
    ) -> ExperimentResultModel:
        """Run coincidence measurement experiment."""
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
        data: CoincidenceMeasurementModel | CoincidenceSummaryModel
        if len(results) > 1:
            true_rates = [r["true_coincidence_rate"] for r in results]
            # Convert TypedDict results to Pydantic models
            measurements = [CoincidenceMeasurementModel.model_validate(r) for r in results]
            data = CoincidenceSummaryModel(
                duration=config.duration,
                repeats=config.repeats,
                mean_true_coincidence_rate=float(np.mean(true_rates)),
                std_true_coincidence_rate=float(np.std(true_rates)),
                measurements=measurements,
            )
        else:
            data = CoincidenceMeasurementModel.model_validate(results[0])

        return ExperimentResultModel(
            config=self._config_model,
            data=data,
            metadata=ExperimentMetadataModel(
                experiment_type="coincidence",
                timestamp=time.time(),
            ),
        )

    def _run_continuous_collection(
        self, cd48: CD48, config: ContinuousExperimentModel
    ) -> ExperimentResultModel:
        """Run continuous data collection experiment."""
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

            counts_data = cd48.get_counts(human_readable=False)
            elapsed = time.time() - start_time
            timestamps.append(elapsed)

            for ch in config.channels:
                if 0 <= ch < len(counts_data["counts"]):
                    channel_data[ch].append(counts_data["counts"][ch])

            self._logger.debug(f"Measurement {i+1}/{num_measurements}: t={elapsed:.1f}s")

        # Convert to rates (counts per second)
        rates: dict[int, list[float]] = {
            ch: [count / config.interval for count in counts] for ch, counts in channel_data.items()
        }

        data = ContinuousDataModel(
            timestamps=timestamps,
            counts=channel_data,
            rates=rates,
            interval=config.interval,
            channels=list(config.channels),
        )

        return ExperimentResultModel(
            config=self._config_model,
            data=data,
            metadata=ExperimentMetadataModel(
                experiment_type="continuous",
                timestamp=time.time(),
            ),
        )

    def _run_voltage_sweep(
        self, cd48: CD48, config: VoltageSweepExperimentModel
    ) -> ExperimentResultModel:
        """Run voltage sweep experiment."""
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
            counts_data = cd48.get_counts(human_readable=False)

            voltage_data.append(float(voltage))
            for ch in config.channels:
                if 0 <= ch < len(counts_data["counts"]):
                    channel_data[ch].append(counts_data["counts"][ch])

            self._logger.debug(f"Voltage {i+1}/{config.voltage_steps}: {voltage:.2f}V")

        # Set DAC back to 0V
        cd48.set_dac_voltage(0.0)

        # Convert to rates
        rates: dict[int, list[float]] = {
            ch: [count / config.measurement_time for count in counts]
            for ch, counts in channel_data.items()
        }

        data = VoltageSweepDataModel(
            voltages=voltage_data,
            counts=channel_data,
            rates=rates,
            measurement_time=config.measurement_time,
            channels=list(config.channels),
        )

        return ExperimentResultModel(
            config=self._config_model,
            data=data,
            metadata=ExperimentMetadataModel(
                experiment_type="voltage_sweep",
                timestamp=time.time(),
            ),
        )

    def _save_results(self, result: ExperimentResultModel) -> None:
        """Save experiment results to file."""
        output = self._config_model.output

        if not output.save_json and not output.save_csv:
            return

        # Create output directory
        output.directory.mkdir(parents=True, exist_ok=True)

        # Generate filename
        exp_name = self._config_model.name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_name = f"{exp_name}_{timestamp}"

        # Save JSON using Pydantic's serialization
        if output.save_json:
            json_path = output.directory / f"{base_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                # Use model_dump for clean JSON serialization
                json.dump(result.model_dump(mode="json"), f, indent=2, default=str)
            self._logger.info(f"Results saved to {json_path}")

        # Save CSV
        if output.save_csv:
            csv_path = output.directory / f"{base_name}.csv"
            self._save_csv(result, csv_path)
            self._logger.info(f"Results saved to {csv_path}")

    def _save_csv(self, result: ExperimentResultModel, path: Path) -> None:
        """Save experiment results to CSV file."""
        import csv

        data = result.data
        exp_type = result.metadata.experiment_type

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if exp_type == "continuous" and isinstance(data, ContinuousDataModel):
                header = ["time"] + [f"ch{ch}_rate" for ch in data.channels]
                writer.writerow(header)

                for i, timestamp in enumerate(data.timestamps):
                    row = [timestamp] + [
                        data.rates[ch][i] if ch in data.rates and i < len(data.rates[ch]) else 0
                        for ch in data.channels
                    ]
                    writer.writerow(row)

            elif exp_type == "voltage_sweep" and isinstance(data, VoltageSweepDataModel):
                header = ["voltage"] + [f"ch{ch}_rate" for ch in data.channels]
                writer.writerow(header)

                for i, voltage in enumerate(data.voltages):
                    row = [voltage] + [
                        data.rates[ch][i] if ch in data.rates and i < len(data.rates[ch]) else 0
                        for ch in data.channels
                    ]
                    writer.writerow(row)

            else:
                # Single measurement or summary format - dump as key-value pairs
                result_dict = result.model_dump(mode="python")
                data_dict = result_dict.get("data", {})
                if isinstance(data_dict, dict):
                    for key, value in data_dict.items():
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
