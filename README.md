# pycd48 - Python Interface for CD48 Coincidence Counter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A comprehensive Python library for controlling the [Red Dog Physics CD48 Coincidence Counter](https://www.reddogphysics.com/cd48.html) via USB serial interface.

## Overview

The **CD48** is a professional 4-channel coincidence counter designed for advanced physics experiments including:
- 🌌 **Cosmic ray detection** and muon lifetime measurements
- 🔬 **Quantum optics** experiments (entanglement, Bell inequalities)
- ⚛️ **Nuclear physics** and particle detection
- 📊 **Multi-detector correlation** studies

This library provides a simple, Pythonic interface to control the device, configure channels, acquire data, and perform sophisticated analysis.

## Features

- 🚀 **Simple Python API** for all CD48 commands
- 🔌 **Auto-detection** of USB serial port
- 🛡️ **Context manager** support for clean resource management
- ⚙️ **Flexible channel configuration** for singles and multi-fold coincidences
- 📊 **Built-in data analysis** tools (statistics, accidental corrections)
- 📈 **Visualization support** with matplotlib integration
- 💾 **Data logging** to CSV and other formats
- 📚 **Comprehensive examples** for various physics experiments
- 🔧 **Hardware control** (trigger levels, impedance, DAC output)
- 🔍 **Full type annotations** for enhanced IDE support and type safety

## Installation

### Prerequisites

- Python 3.7 or higher
- USB serial drivers (usually pre-installed on modern systems)

### Install from source

```bash
git clone https://github.com/OpenPhysics/pycd48.git
cd pycd48
pip install -e .
```

### Install dependencies only

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from pycd48 import CD48
import time

# Connect to CD48 (auto-detects port)
with CD48() as cd48:
    # Configure channel 0 to count singles on input A
    cd48.set_channel(0, A=1, B=0, C=0, D=0)

    # Configure channel 4 to count A-B coincidences
    cd48.set_channel(4, A=1, B=1, C=0, D=0)

    # Set trigger level to 0.5V
    cd48.set_trigger_level(0.5)

    # Set 50 Ohm input impedance
    cd48.set_impedance_50ohm()

    # Clear counters and count for 10 seconds
    cd48.clear_counts()
    time.sleep(10)

    # Read results
    data = cd48.get_counts(human_readable=False)
    print(f"Channel A: {data['counts'][0]} counts")
    print(f"A-B coincidences: {data['counts'][4]} counts")
```

## Hardware Setup

The CD48 connects via USB and appears as a virtual COM port. The device uses:
- **Baudrate**: 115200 (default)
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1

### Linux Permissions

On Linux, you may need to add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and log back in for the change to take effect.

## CD48 Class Reference

### Connection

```python
CD48(port=None, baudrate=115200, timeout=1)
```

- `port`: Serial port name (auto-detects if None)
- `baudrate`: Communication speed (default: 115200)
- `timeout`: Read timeout in seconds

### Methods

#### Configuration

- **`set_channel(channel, A, B, C, D)`**: Configure counter channel
  - `channel`: Counter number (0-7)
  - `A, B, C, D`: Input enables (0 or 1)
  - Example: `set_channel(4, A=1, B=1, C=0, D=0)` configures counter 4 for A-B coincidences

- **`set_trigger_level(voltage)`**: Set trigger threshold
  - `voltage`: Threshold voltage (0.0 to 4.08V)

- **`set_impedance_50ohm()`**: Set inputs to 50Ω impedance

- **`set_impedance_highz()`**: Set inputs to high-Z impedance

- **`set_dac_voltage(voltage)`**: Set DAC output voltage
  - `voltage`: Output voltage (0.0 to 4.08V)

#### Data Acquisition

- **`get_counts(human_readable=True)`**: Read current counts
  - Returns formatted string if `human_readable=True`
  - Returns dict with `counts` list and `overflow` flag if `False`

- **`clear_counts()`**: Clear all counters (reads and resets)

- **`get_overflow()`**: Check counter overflow status
  - Returns 8-bit flag (bit n = counter n overflowed)

#### Automatic Reporting

- **`set_repeat(interval_ms)`**: Set auto-report interval
  - `interval_ms`: Reporting interval (100-65535 ms)

- **`toggle_repeat()`**: Toggle auto-reporting on/off

#### Device Information

- **`get_settings(human_readable=True)`**: Get current configuration

- **`get_version()`**: Get firmware version

- **`test_leds()`**: Test all LEDs (lights for 1 second)

- **`help()`**: Get built-in command help

#### Connection Management

- **`close()`**: Close serial connection

The CD48 class supports context managers:

```python
with CD48() as cd48:
    # Use device
    pass
# Automatically closes connection
```

### Serial Command Reference

For advanced users, here are the low-level serial commands used by the CD48:

| Command | Parameters | Function | Python Method |
|---------|-----------|----------|---------------|
| `c` | None | Get counts (machine-readable) | `get_counts(human_readable=False)` |
| `C` | None | Get counts (pretty-print) | `get_counts(human_readable=True)` |
| `E` | None | Get overflow status and clear | `get_overflow()` |
| `H` | None | Display help text | `help()` |
| `L###` | 0-255 | Set trigger level (byte value) | `set_trigger_level(voltage)` |
| `p` | None | Get settings (machine-readable) | `get_settings(human_readable=False)` |
| `P` | None | Get settings (pretty-print) | `get_settings(human_readable=True)` |
| `r####` | 100-65535 | Set repeat interval (ms) | `set_repeat(interval_ms)` |
| `R` | None | Toggle repeat mode | `toggle_repeat()` |
| `S#####` | Counter+ABCD | Set channel configuration | `set_channel(ch, A, B, C, D)` |
| `T` | None | Test all LEDs | `test_leds()` |
| `v` | None | Get firmware version | `get_version()` |
| `V###` | 0-255 | Set DAC voltage (byte value) | `set_dac_voltage(voltage)` |
| `z` | None | Set 50Ω impedance | `set_impedance_50ohm()` |
| `Z` | None | Set high-Z impedance | `set_impedance_highz()` |

**Note**: Commands are sent with a carriage return (`\r`). Case matters for some commands.

## Examples

The library includes comprehensive examples for various use cases. See the [examples directory](examples/) for complete code.

### Example 1: Device Information
Test connection and display device info:
```bash
python examples/device_info.py
```

### Example 2: Simple Counting
Count singles and coincidences on multiple channels:
```bash
python examples/simple_counting.py
```

### Example 3: Continuous Data Collection
Monitor and plot count rates over time with statistical analysis:
```bash
python examples/continuous_collection.py
```

### Example 4: Cosmic Ray Detection
Configure for cosmic ray telescope with multiple detectors:
```bash
python examples/cosmic_ray_telescope.py
```

### Example 5: Trigger Level Calibration
Automatically find optimal trigger threshold for your detectors:
```bash
python examples/calibrate_trigger.py
```

### Example 6: Data Logging
Log continuous data to CSV for long-term measurements:
```bash
python examples/data_logger.py
```

### Example 7: Accidental Coincidence Analysis
Detailed analysis of true vs. accidental coincidences:
```bash
python examples/accidental_analysis.py

### Example 8: Real-time Monitor (Repeat Mode)
Real-time monitoring using automatic repeat mode:
```bash
python examples/realtime_monitor.py
```

### Example 9: Voltage Sweep (DAC Control)
Automated voltage sweep using DAC output for equipment control:
```bash
python examples/voltage_sweep.py
```

### Example 10: Overflow Detection
Counter overflow detection and adaptive measurement:
```bash
python examples/overflow_demo.py
```
```

See the [examples README](examples/README.md) for detailed descriptions of each example.

## Common Channel Configurations

```python
# Singles counting
cd48.set_channel(0, A=1, B=0, C=0, D=0)  # Count A singles
cd48.set_channel(1, A=0, B=1, C=0, D=0)  # Count B singles

# Two-fold coincidences
cd48.set_channel(4, A=1, B=1, C=0, D=0)  # A AND B
cd48.set_channel(5, A=1, B=0, C=1, D=0)  # A AND C

# Three-fold coincidences
cd48.set_channel(7, A=1, B=1, C=1, D=0)  # A AND B AND C

# Anti-coincidence (requires external logic)
# The CD48 only does AND logic; anti-coincidence requires
# external circuitry or post-processing
```

## Timing and Coincidence Windows

The CD48 has a fixed coincidence window of approximately **25 nanoseconds** (time resolution based on edge detection). Events on selected channels must occur within this window to be counted as a coincidence.

### Accidental Coincidence Correction

Random coincidences can occur between uncorrelated sources. The expected accidental rate is:

```
R_acc = 2 × τ × R_A × R_B
```

where:
- `τ` = coincidence window (~25 ns)
- `R_A`, `R_B` = singles rates on channels A and B

See `examples/continuous_collection.py` and `examples/accidental_analysis.py` for implementation.

## Troubleshooting

### Device not found

- Verify USB connection
- Check that drivers are installed
- Try specifying port manually: `CD48(port='/dev/ttyUSB0')`

### Permission denied (Linux)

```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### No data / zero counts

- Check trigger level (try different values)
- Verify input impedance setting matches your source
- Check that channels are configured correctly
- Ensure input signals are connected

### Counter overflow

- Reduce measurement interval
- Use higher sample rate to prevent overflow
- Check overflow status with `get_overflow()`

## Technical Specifications

- **Input channels**: 4 (A, B, C, D) BNC connectors
- **Counters**: 8 independently configurable
  - Counters 0-6: 24-bit (max count: 16,777,215)
  - Counter 7: 16-bit (max count: 65,535)
- **Coincidence window**: ~25 ns (edge detection based, tested <±30 ns)
- **Time resolution**: Typically 25 nanoseconds
- **Trigger threshold**: 0-4.08V (8-bit: 0-255), adjustable
- **DAC output**: 0-4.08V (8-bit: 0-255), for experiment control
- **Input impedance**: 50Ω or High-Z (selectable)
- **Interface**: USB virtual COM port (Cypress PSoC5)
- **Baudrate**: 115200
- **LED indicators**: Input activity, counter activity, overflow, communications, data status
- **Configuration persistence**: Settings saved across power cycles

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development

The codebase includes comprehensive type annotations for improved code quality and IDE support.

**Type Checking:**

Run mypy to verify type correctness:
```bash
mypy pycd48/ tests/
```

**Running Tests:**

```bash
pytest tests/
```

**Code Quality:**

The project uses:
- Full type annotations (PEP 484) with TypedDict for structured data
- Function overloads for precise type inference
- Mypy for static type checking

## Use Cases

### Cosmic Ray Detection
The CD48 is ideal for cosmic ray experiments:
- Measure muon flux rates at different altitudes
- Build multi-detector telescopes for directional measurements
- Study cosmic ray correlations and timing

### Quantum Optics
Perfect for quantum mechanics experiments:
- Photon coincidence counting for entangled photon pairs
- Bell inequality tests
- Quantum key distribution (QKD) demonstrations

### Nuclear and Particle Physics
Professional-grade counting for radiation detection:
- Gamma-gamma coincidence spectroscopy
- Beta-gamma correlation measurements
- Multi-detector nuclear decay studies

### Educational Laboratories
Excellent for teaching advanced physics concepts:
- Statistical analysis of random processes
- Coincidence timing and correlation
- Data acquisition and analysis techniques

## Links and Resources

- 🏢 [Red Dog Physics](https://www.reddogphysics.com/) - Manufacturer
- 📦 [CD48 Product Page](https://www.reddogphysics.com/cd48.html) - Official hardware documentation
- 💻 [GitHub Repository](https://github.com/OpenPhysics/pycd48) - Source code and issues
- 📖 [API Documentation](https://github.com/OpenPhysics/pycd48#cd48-class-reference) - Complete API reference

## Citation

If you use this library in your research, please cite:

```bibtex
@software{pycd48,
  title = {pycd48: Python Interface for CD48 Coincidence Counter},
  author = {OpenPhysics Contributors},
  year = {2026},
  url = {https://github.com/OpenPhysics/pycd48},
  note = {Python library for Red Dog Physics CD48}
}
```

## Acknowledgments

This library is based on the CD48 USB command protocol developed by [Red Dog Physics](https://www.reddogphysics.com/). The CD48 hardware is designed and manufactured by Red Dog Physics. For hardware specifications, manuals, and purchasing information, visit the [official CD48 product page](https://www.reddogphysics.com/cd48.html).
