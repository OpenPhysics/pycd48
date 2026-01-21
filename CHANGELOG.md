# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Unit tests for CD48 class with mocked serial communication
- GitHub Actions CI/CD pipeline
- Contributing guidelines (CONTRIBUTING.md)
- This CHANGELOG file
- Code quality tools integration (black, ruff, mypy)

## [0.1.0] - 2026-01-15

### Added
- Initial release of pycd48
- Complete CD48 class implementation with all serial commands
- Auto-detection of USB serial ports
- Context manager support
- 10 comprehensive example scripts:
  - device_info.py - Device information and testing
  - simple_counting.py - Basic counting operations
  - continuous_collection.py - Time-resolved data collection
  - cosmic_ray_telescope.py - Cosmic ray muon detection
  - calibrate_trigger.py - Automatic trigger threshold calibration
  - data_logger.py - CSV data logging
  - accidental_analysis.py - Coincidence analysis
  - realtime_monitor.py - Real-time monitoring with repeat mode
  - voltage_sweep.py - DAC voltage sweep for equipment control
  - overflow_demo.py - Counter overflow detection
- Comprehensive documentation in README.md
- Example-specific documentation in examples/README.md
- Serial command reference table
- Application-specific guides (cosmic rays, quantum optics, nuclear physics, education)
- Citation format for academic use

### Technical Specifications
- Accurate to official CD48 manual
- Coincidence window: 25 ns
- Counter depths: 24-bit (ch 0-6), 16-bit (ch 7)
- Voltage range: 0-4.08V
- All 15 serial commands implemented

[Unreleased]: https://github.com/OpenPhysics/pycd48/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/OpenPhysics/pycd48/releases/tag/v0.1.0
