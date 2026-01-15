# pycd48 - Python Interface for CD48 Coincidence Counter

A Python library for controlling the Red Dog Physics CD48 Coincidence Counter via USB serial interface.

## Overview

The CD48 is a multi-channel coincidence counter designed for physics experiments, particularly cosmic ray detection and quantum optics. This library provides a simple Python interface to control the device, configure channels, and acquire data.

## Features

- Simple Python API for all CD48 commands
- Auto-detection of USB serial port
- Context manager support for clean resource management
- Configurable channel mappings for singles and coincidence counting
- Support for all 8 input channels and counter configurations
- Examples for common use cases

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

## Examples

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

This example:
- Configures 8 counters for various combinations
- Counts for 10 seconds
- Displays results and calculates rates

### Example 3: Continuous Data Collection

Monitor and plot count rates over time:

```bash
python examples/continuous_collection.py
```

This example:
- Collects data over 60 seconds
- Calculates statistics and accidental coincidence rates
- Generates time series and histogram plots

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

The CD48 has a fixed coincidence window of approximately **10 nanoseconds**. Events on selected channels must occur within this window to be counted as a coincidence.

### Accidental Coincidence Correction

Random coincidences can occur between uncorrelated sources. The expected accidental rate is:

```
R_acc = 2 × τ × R_A × R_B
```

where:
- `τ` = coincidence window (~10 ns)
- `R_A`, `R_B` = singles rates on channels A and B

See `examples/continuous_collection.py` for implementation.

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

- **Input channels**: 4 (A, B, C, D)
- **Counters**: 8 configurable
- **Count depth**: 32-bit (4,294,967,295 max)
- **Coincidence window**: ~10 ns
- **Trigger range**: 0-4.08V
- **Input impedance**: 50Ω or High-Z (selectable)
- **Interface**: USB virtual COM port
- **Baudrate**: 115200

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Links

- [Red Dog Physics](http://reddogphysics.com/) - Manufacturer
- [CD48 Product Page](http://reddogphysics.com/cd48.html)
- [GitHub Repository](https://github.com/OpenPhysics/pycd48)

## Acknowledgments

Based on the CD48 USB command protocol developed by Red Dog Physics.
