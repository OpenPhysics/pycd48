# CD48 Examples

This directory contains example scripts demonstrating how to use the pycd48 library.

## Examples

### 1. device_info.py

**Purpose**: Test connection and display device information

**Usage**:
```bash
python device_info.py
```

**What it does**:
- Connects to the CD48
- Displays firmware version
- Shows current settings
- Lists available commands
- Tests the LEDs

**Good for**: Verifying your setup works correctly

---

### 2. simple_counting.py

**Purpose**: Basic counting and coincidence measurement

**Usage**:
```bash
python simple_counting.py
```

**What it does**:
- Configures all 8 counters for various channel combinations
- Counts for 10 seconds
- Displays total counts and count rates
- Shows singles on all 4 inputs
- Shows 2-fold and 3-fold coincidences

**Good for**: Learning basic data acquisition

---

### 3. continuous_collection.py

**Purpose**: Time-resolved data collection and analysis

**Usage**:
```bash
python continuous_collection.py
```

**What it does**:
- Collects data continuously for 60 seconds (1-second intervals)
- Monitors channels A, B, and A-B coincidences
- Calculates statistics (mean, standard deviation)
- Estimates accidental coincidence rate
- Generates plots:
  - Time series of count rates
  - Histogram distributions
- Saves plot as `cd48_data.png`

**Good for**:
- Monitoring stability
- Statistical analysis
- Understanding coincidence corrections

---

## Customizing the Examples

All examples can be easily modified for your experiment:

### Change measurement duration:
```python
duration = 30  # Count for 30 seconds instead of 10
```

### Change interval:
```python
interval = 0.5  # Sample every 0.5 seconds
```

### Specify serial port:
```python
with CD48(port='/dev/ttyUSB0') as cd48:  # Linux
# or
with CD48(port='COM3') as cd48:  # Windows
```

### Change trigger level:
```python
cd48.set_trigger_level(0.3)  # Lower threshold for weaker signals
cd48.set_trigger_level(1.0)  # Higher threshold to reduce noise
```

### Configure different channels:
```python
# Example: 4-fold coincidence
cd48.set_channel(0, A=1, B=1, C=1, D=1)  # Count A AND B AND C AND D
```

## Tips

1. **Start with device_info.py** to verify everything is connected properly

2. **Use simple_counting.py** to find optimal trigger levels and verify signal quality

3. **Use continuous_collection.py** for actual experiments and data analysis

4. **Save your data** by modifying the examples to write to CSV:
   ```python
   import csv
   with open('data.csv', 'w', newline='') as f:
       writer = csv.writer(f)
       writer.writerow(['Time', 'ChannelA', 'ChannelB', 'Coincidences'])
       writer.writerows(zip(times, counts_A, counts_B, coincidences))
   ```

## Common Issues

**Import Error**: Make sure pycd48 is installed:
```bash
cd ..
pip install -e .
```

**No device found**: Specify port manually in the example code

**Permission denied** (Linux): Add your user to dialout group:
```bash
sudo usermod -a -G dialout $USER
```
