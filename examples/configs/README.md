# CD48 YAML Experiment Configurations

This directory contains example YAML configuration files for common CD48 experiments. Using YAML configs provides:

- **Better reproducibility**: Share exact experiment parameters
- **Easier collaboration**: Non-programmers can modify experiment settings
- **Version control**: Track changes to experimental setups

## Quick Start

### Install YAML support

```bash
pip install pycd48[yaml]
# or
pip install pyyaml
```

### Run an experiment

```bash
python ../run_yaml_experiment.py configs/simple_coincidence.yaml
```

Or in Python:

```python
from pycd48 import run_experiment

result = run_experiment("configs/simple_coincidence.yaml")
print(f"Coincidence rate: {result['data']['coincidence_rate']:.2f} Hz")
```

## Configuration File Structure

A YAML configuration file has four main sections:

```yaml
# Experiment metadata
name: my_experiment
description: Brief description of what this measures

# Device connection settings
connection:
  port: /dev/ttyUSB0  # Optional, auto-detect if omitted
  baudrate: 115200
  timeout: 1.0
  init_delay: 2.0

# Device configuration
settings:
  trigger_level: 0.5  # Volts
  impedance: 50ohm    # or "highz"
  dac_voltage: 2.0    # Optional DAC output

  # Channel configuration
  channels:
    "0":  # Channel number (as string)
      A: 1  # Monitor input A
      B: 0
      C: 0
      D: 0
    "4":  # A-B coincidence channel
      A: 1
      B: 1
      C: 0
      D: 0

# Experiment parameters (type-specific)
experiment:
  type: coincidence  # rate, coincidence, continuous, voltage_sweep
  duration: 60.0
  # ... type-specific parameters

# Output settings
output:
  directory: ./data
  csv: true
  json: true
```

## Experiment Types

### 1. Rate Measurement (`rate_measurement.yaml`)

Simple count rate measurement on a single channel.

**Experiment parameters:**
```yaml
experiment:
  type: rate
  channel: 0        # Channel to measure
  duration: 10.0    # Seconds per measurement
  repeats: 10       # Number of measurements
```

**Use for:**
- Quick detector checks
- Background rate measurements
- Single detector characterization

---

### 2. Coincidence Measurement (`simple_coincidence.yaml`)

Two-detector coincidence with accidental correction.

**Experiment parameters:**
```yaml
experiment:
  type: coincidence
  duration: 60.0              # Measurement duration
  singles_a_channel: 0        # Singles A channel
  singles_b_channel: 1        # Singles B channel
  coincidence_channel: 4      # A-B coincidence channel
  coincidence_window: 25.0e-9 # Coincidence window (seconds)
  repeats: 5                  # Number of measurements
```

**Use for:**
- Basic coincidence experiments
- Testing detector pairs
- Accidental coincidence analysis

---

### 3. Continuous Collection (`cosmic_ray_telescope.yaml`, `continuous_monitoring.yaml`)

Long-term continuous data collection.

**Experiment parameters:**
```yaml
experiment:
  type: continuous
  duration: 300      # Total duration (seconds)
  interval: 5        # Measurement interval (seconds)
  channels: [0, 1, 4]  # Channels to monitor
```

**Use for:**
- Cosmic ray telescope measurements
- Long-term monitoring
- Time-series analysis
- Environmental radiation monitoring

---

### 4. Voltage Sweep (`voltage_sweep.yaml`)

Automated voltage sweep using DAC output.

**Experiment parameters:**
```yaml
experiment:
  type: voltage_sweep
  voltage_min: 0.0      # Starting voltage
  voltage_max: 4.0      # Ending voltage
  voltage_steps: 20     # Number of points
  measurement_time: 5.0 # Seconds per point
  channels: [0, 1, 4]   # Channels to monitor
```

**Use for:**
- PMT high voltage optimization
- Detector characterization
- Finding optimal operating points

## Output Files

When `output` is configured, results are saved automatically:

```yaml
output:
  directory: ./data  # Output directory (created if needed)
  csv: true         # Save as CSV (easy plotting)
  json: true        # Save as JSON (full details)
```

Files are named: `{experiment_name}_{timestamp}.{csv|json}`

### CSV Format

**Continuous/Voltage Sweep:**
```csv
time,ch0_rate,ch1_rate,ch4_rate
0.0,1234.5,2345.6,123.4
5.0,1235.2,2344.1,124.2
...
```

**Single Measurements:**
```csv
parameter,value
mean_rate,1234.56
std_rate,12.34
...
```

### JSON Format

Complete experiment record including:
- Full configuration
- All measurement data
- Metadata (timestamp, type, etc.)

## Further Reading

- See `../run_yaml_experiment.py` for programmatic usage
- Main documentation: `../../README.md`
- API reference: Use `help(pycd48.run_experiment)` in Python
