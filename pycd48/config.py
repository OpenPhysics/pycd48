"""
Unified configuration handling for CD48.

This module provides common configuration loading and settings
application logic used across CD48 implementations.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .constants import DEFAULT_BAUDRATE, DEFAULT_TIMEOUT

if TYPE_CHECKING:
    from .protocols import SettingsApplicable

_logger = logging.getLogger(__name__)


class CD48ConfigError(Exception):
    """Raised when configuration file is invalid."""

    pass


def load_config_file(config_path: Path) -> dict[str, object]:
    """
    Load configuration from JSON or YAML file.

    Parameters:
    -----------
    config_path : Path
        Path to the configuration file

    Returns:
    --------
    dict : Parsed configuration dictionary

    Raises:
    -------
    CD48ConfigError
        If the file format is unsupported or parsing fails
    """
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
                    "PyYAML is required for YAML config files. " "Install with: pip install pyyaml"
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


def extract_connection_settings(
    config: dict[str, object],
    default_baudrate: int = DEFAULT_BAUDRATE,
    default_timeout: float = DEFAULT_TIMEOUT,
) -> tuple[str | None, int, float, float | None, bool]:
    """
    Extract connection settings from configuration dictionary.

    Parameters:
    -----------
    config : dict
        Configuration dictionary
    default_baudrate : int
        Default baud rate if not specified
    default_timeout : float
        Default timeout if not specified

    Returns:
    --------
    tuple : (port, baudrate, timeout, init_delay, strict_mode)
    """
    connection_raw = config.get("connection", {})
    connection = connection_raw if isinstance(connection_raw, dict) else {}

    port_val = connection.get("port")
    port: str | None = str(port_val) if port_val is not None else None

    baudrate_val = connection.get("baudrate", default_baudrate)
    baudrate: int = (
        int(baudrate_val) if isinstance(baudrate_val, (int, float)) else default_baudrate
    )

    timeout_val = connection.get("timeout", default_timeout)
    timeout: float = (
        float(timeout_val) if isinstance(timeout_val, (int, float)) else default_timeout
    )

    init_delay_val = connection.get("init_delay")
    init_delay: float | None = (
        float(init_delay_val) if isinstance(init_delay_val, (int, float)) else None
    )

    strict_mode_val = connection.get("strict_mode", False)
    strict_mode: bool = bool(strict_mode_val) if strict_mode_val is not None else False

    return port, baudrate, timeout, init_delay, strict_mode


def apply_settings(
    device: SettingsApplicable,
    settings: dict[str, object],
    logger: logging.Logger | None = None,
) -> None:
    """
    Apply device settings from configuration dictionary.

    This function applies trigger level, impedance, DAC voltage, and
    channel configuration settings to a CD48 device.

    Parameters:
    -----------
    device : SettingsApplicable
        Device instance that supports settings methods
    settings : dict
        Settings dictionary from configuration
    logger : logging.Logger, optional
        Logger instance for warnings
    """
    log = logger or _logger

    # Set trigger level
    if "trigger_level" in settings:
        trigger = settings["trigger_level"]
        if isinstance(trigger, (int, float)):
            device.set_trigger_level(float(trigger))

    # Set impedance
    if "impedance" in settings:
        impedance = settings["impedance"]
        if impedance == "50ohm":
            device.set_impedance_50ohm()
        elif impedance == "highz" or impedance == "1Mohm":
            device.set_impedance_highz()
        else:
            log.warning(f"Unknown impedance setting: {impedance}")

    # Set DAC voltage
    if "dac_voltage" in settings:
        dac = settings["dac_voltage"]
        if isinstance(dac, (int, float)):
            device.set_dac_voltage(float(dac))

    # Configure channels
    if "channels" in settings:
        channels = settings["channels"]
        if isinstance(channels, dict):
            for ch_str, ch_config in channels.items():
                try:
                    ch_num = int(ch_str)
                    if isinstance(ch_config, dict):
                        device.set_channel(
                            ch_num,
                            A=int(ch_config.get("A", 0)),
                            B=int(ch_config.get("B", 0)),
                            C=int(ch_config.get("C", 0)),
                            D=int(ch_config.get("D", 0)),
                        )
                except (ValueError, TypeError) as e:
                    log.warning(f"Invalid channel config {ch_str}: {e}")
