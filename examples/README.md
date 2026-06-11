# CD48 Examples

This directory contains comprehensive example scripts demonstrating how to use the pycd48 library for various physics experiments and applications.

## Interactive Tutorial (Jupyter Notebook)

### pycd48_tutorial.ipynb 📓

**Best starting point for new users!**

An interactive Jupyter notebook that provides a comprehensive tutorial covering all major features of the pycd48 library.

**Usage**:
```bash
jupyter notebook pycd48_tutorial.ipynb
# or
jupyter lab pycd48_tutorial.ipynb
```

**What it includes**:
- 📖 Introduction to the CD48 and its capabilities
- 🔌 Device connection and configuration
- 📊 Simple and continuous data collection
- 📈 Real-time data visualization with matplotlib
- 🧮 Statistical analysis and accidental coincidence calculations
- 🎛️ Advanced features (DAC control, overflow detection, data logging)
- 💡 Interactive code cells with detailed explanations
- 🎨 Publication-quality plots and visualizations

**Perfect for**:
- Learning the library interactively
- Experimenting with different configurations
- Teaching and educational demonstrations
- Rapid prototyping of experiments
- Creating custom analysis workflows

**Prerequisites**: Install Jupyter separately (`pip install jupyter` or `uv pip install jupyter`)

---

## Quick Start

If you're new to the CD48, follow this recommended order:

1. **pycd48_tutorial.ipynb** - Interactive tutorial (recommended start!)
2. **device_info.py** - Verify your connection works
3. **simple_counting.py** - Learn basic counting operations
4. **calibrate_trigger.py** - Find optimal trigger levels for your detectors
5. **continuous_collection.py** - Understand time-resolved measurements
6. Then explore the advanced examples based on your application

## Basic Examples

### 1. device_info.py

**Purpose**: Test connection and display device information

**Usage**:
```bash
python device_info.py
```

**What it does**:
- Auto-detects and connects to the CD48
- Displays firmware version and device info
- Shows current configuration settings
- Lists all available commands
- Tests the LED indicators

**Perfect for**:
- First-time setup verification
- Troubleshooting connection issues
- Quick device health check

**Duration**: ~5 seconds

---

### 2. simple_counting.py

**Purpose**: Basic counting and coincidence measurement

**Usage**:
```bash
python simple_counting.py
```

**What it does**:
- Configures all 8 counters for various channel combinations
- Measures for 10 seconds with fixed trigger level
- Displays total counts and count rates for:
  - Singles on all 4 input channels
  - 2-fold coincidences (A-B, A-C, B-C)
  - 3-fold coincidences (A-B-C)
- Shows overflow warnings if counters saturate

**Perfect for**:
- Learning basic data acquisition
- Verifying detector signals
- Quick signal quality check

**Duration**: ~10 seconds

---

### 3. continuous_collection.py

**Purpose**: Time-resolved data collection with visualization

**Usage**:
```bash
python continuous_collection.py
```

**What it does**:
- Collects data continuously for 60 seconds (1-second intervals)
- Monitors channels A, B, and A-B coincidences
- Calculates comprehensive statistics (mean, std, accidental rate)
- Generates publication-quality plots:
  - Time series of count rates
  - Distribution histograms
- Estimates true vs accidental coincidences
- Saves results as `cd48_data.png`

**Perfect for**:
- Monitoring detector stability over time
- Statistical analysis of count rates
- Understanding accidental coincidence corrections
- Preparing data for reports

**Duration**: ~60 seconds

---

## Advanced Examples

### 4. cosmic_ray_telescope.py

**Purpose**: Cosmic ray muon detection with multi-detector telescope

**Usage**:
```bash
python cosmic_ray_telescope.py
```

**What it does**:
- Configures a vertical cosmic ray telescope with multiple detectors
- Measures singles on 4 detectors (top, middle, bottom, background)
- Counts 2-fold and 3-fold coincidences
- Calculates telescope efficiency
- Estimates muon flux (particles/m²·s)
- Performs accidental coincidence corrections
- Generates comprehensive analysis plots:
  - Singles rates over time
  - Coincidence rates with statistical uncertainty
  - Rate distributions
  - Correlation analysis
- Saves timestamped results

**Perfect for**:
- Cosmic ray physics experiments
- Educational muon lifetime measurements
- Multi-detector correlation studies
- Testing detector alignment and efficiency

**Typical setup**:
```
Detector A (top)
     ↓ muon path
Detector C (middle)
     ↓
Detector B (bottom)
Detector D (background, side)
```

**Duration**: ~5 minutes (configurable)

---

### 5. calibrate_trigger.py

**Purpose**: Automatic trigger threshold calibration and optimization

**Usage**:
```bash
python calibrate_trigger.py
```

**What it does**:
- Scans trigger voltage from 0.1V to 2.0V in small steps
- Measures count rate at each threshold level
- Identifies the "knee" in the rate curve (noise threshold)
- Provides recommended trigger levels for each channel
- Generates diagnostic plots:
  - Count rate vs trigger voltage (log scale)
  - Normalized rates for easy comparison
  - Marks optimal threshold points
- Saves results as `trigger_calibration.png`

**Perfect for**:
- Finding optimal trigger levels for new detectors
- Characterizing detector noise levels
- Ensuring consistent thresholds across channels
- Troubleshooting low signal-to-noise ratio

**Duration**: ~1-2 minutes (depends on voltage range)

**Tips**:
- Run with detectors connected but no source for noise characterization
- Run with source present to find signal threshold
- Compare results between channels to match detector sensitivities

---

### 6. data_logger.py

**Purpose**: Continuous data logging to CSV for long-term measurements

**Usage**:
```bash
python data_logger.py
```

**What it does**:
- Creates timestamped CSV files in `data/` directory
- Logs all 8 channels plus overflow flags continuously
- Supports indefinite runtime (Ctrl+C to stop)
- Provides real-time console display of key channels
- Flushes data to disk periodically (every 10 measurements)
- Handles graceful shutdown to prevent data loss
- Reports total measurements and file size on exit

**CSV Format**:
```
Timestamp, Elapsed_Time_s, Ch0_A_singles, Ch1_B_singles, ..., Overflow_Flag
2026-01-15 10:30:00.123, 0.000, 1234, 1189, ...
```

**Perfect for**:
- Long-term stability monitoring
- Overnight measurements
- Building large datasets for statistical analysis
- Continuous environmental monitoring

**Duration**: Continuous (until stopped)

**Configurable parameters**:
- Measurement interval (default: 1 second)
- Total duration (default: unlimited)
- Display update frequency

---

### 7. accidental_analysis.py

**Purpose**: Detailed analysis of true vs accidental coincidences

**Usage**:
```bash
python accidental_analysis.py
```

**What it does**:
- Collects 30 samples with 2-second integration each
- Analyzes singles and coincidence rates statistically
- Calculates expected accidental coincidence rates using:
  - R_acc = 2 × τ × R_A × R_B (for 2-fold)
  - R_acc ≈ 3 × τ × R_A × R_B × R_C (for 3-fold)
- Determines true coincidence rates
- Computes statistical significance (σ)
- Provides interpretation and warnings
- Generates comprehensive analysis plots:
  - Time series of all rates
  - Coincidence breakdown (measured/accidental/true)
  - Distribution analysis
  - Correlation plots (singles product vs coincidences)
- Saves results as `accidental_analysis.png`

**Perfect for**:
- Verifying detector correlation
- Understanding systematic errors
- Quantum optics entanglement verification
- Nuclear correlation measurements
- Educational demonstrations

**Duration**: ~60 seconds (30 × 2s measurements)

**Interpretation guide**:
- Accidental fraction < 10%: Excellent, true coincidences dominate
- Accidental fraction 10-50%: Moderate, correction is important
- Accidental fraction > 50%: Poor, consider improving setup
- Significance > 5σ: Highly significant correlation
- Significance > 3σ: Significant correlation
- Significance < 3σ: Increase measurement time

---

### 8. realtime_monitor.py

**Purpose**: Real-time monitoring using automatic repeat mode

**Usage**:
```bash
python realtime_monitor.py
```

**What it does**:
- Enables CD48's automatic repeat mode
- Device sends count data at set intervals (e.g., every 1 second)
- Displays real-time data stream
- Reduces USB communication overhead
- No polling required - data pushed automatically from device

**Perfect for**:
- Real-time monitoring dashboards
- Continuous data streaming
- Reducing CPU usage during long measurements
- Synchronized data acquisition

**Duration**: Continuous (until stopped)

**Key feature**: Uses the `r` (set interval) and `R` (toggle) commands for automatic reporting

---

### 9. voltage_sweep.py

**Purpose**: Automated voltage sweep using DAC output

**Usage**:
```bash
python voltage_sweep.py
```

**What it does**:
- Sweeps DAC output voltage from 0-4V
- Measures count rates at each voltage
- Finds optimal operating voltage
- Calculates signal-to-noise ratio
- Generates comprehensive analysis plots:
  - Count rates vs voltage
  - Coincidence rate optimization
  - S/N ratio analysis
  - Total counts comparison
- Saves results as `voltage_sweep.png`

**Perfect for**:
- PMT high voltage optimization
- Detector bias voltage scanning
- Automated equipment control
- Finding optimal operating points
- Experiment automation

**Duration**: Configurable (default ~1 minute for 20 points)

**Key feature**: Uses the `V` command to control external equipment via DAC output (0-4.08V)

**Typical use case**: Connect DAC output to PMT power supply control input to find optimal voltage for maximum coincidence rate

---

### 10. overflow_demo.py

**Purpose**: Counter overflow detection and adaptive measurement

**Usage**:
```bash
python overflow_demo.py
```

**What it does**:
- Demonstrates counter overflow detection
- Decodes which specific counters overflowed
- Shows difference between 24-bit and 16-bit counters
- Implements adaptive interval adjustment
- Automatically reduces interval when approaching overflow
- Calculates safe measurement intervals for various count rates
- Provides best practices and recommendations

**Perfect for**:
- High count rate measurements
- Learning counter limitations
- Preventing data loss
- Understanding when to use which counter

**Duration**: ~30 seconds (configurable)

**Key feature**: Uses the `E` command to check and clear overflow flags

**Important notes**:
- Counters 0-6: 24-bit (max 16,777,215)
- Counter 7: 16-bit (max 65,535) - use for rare events only!
- At 1 MHz: Counter 7 overflows in 0.065 seconds!

---

### 11. run_yaml_experiment.py

**Purpose**: Run reproducible experiments from YAML configuration files

**Usage**:
```bash
pip install pycd48[yaml]
python run_yaml_experiment.py configs/simple_coincidence.yaml
```

**What it does**:
- Loads experiment parameters from YAML (channels, trigger levels, measurement duration)
- Runs the experiment using `run_experiment()` from the library
- Prints structured results (counts, rates, coincidence statistics)
- Supports all configs in `configs/` (coincidence, rate measurement, voltage sweep, etc.)

**Perfect for**:
- Reproducible experiment workflows
- Sharing experiment setups with collaborators
- Batch runs across multiple configurations

**Prerequisites**: `pip install pycd48[yaml]` (includes PyYAML and Pydantic)

See [configs/README.md](configs/README.md) for YAML format details.

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

## Application-Specific Guides

### For Cosmic Ray Experiments
1. Start with `calibrate_trigger.py` to find optimal thresholds
2. Use `cosmic_ray_telescope.py` for data collection
3. Switch to `data_logger.py` for overnight runs
4. Analyze correlation with `accidental_analysis.py`

### For Quantum Optics
1. Verify detector signals with `simple_counting.py`
2. Optimize thresholds with `calibrate_trigger.py`
3. Use `accidental_analysis.py` to verify entanglement
4. Long measurements with `data_logger.py`

### For Nuclear/Particle Physics
1. Check detector response with `device_info.py`
2. Calibrate discriminators with `calibrate_trigger.py`
3. Collect correlation data with `continuous_collection.py`
4. Detailed analysis with `accidental_analysis.py`

### For Educational Labs
1. Start with `device_info.py` for student familiarization
2. Learn basics with `simple_counting.py`
3. Demonstrate statistics with `continuous_collection.py`
4. Teach coincidence corrections with `accidental_analysis.py`

---

## Tips and Best Practices

### Getting Started
1. **Always start with device_info.py** to verify the connection
2. **Use calibrate_trigger.py** before any serious measurements
3. **Test with simple_counting.py** before long runs
4. **Use data_logger.py** for production measurements

### Optimization
- **Trigger levels**: Too low → noise, too high → miss events
- **Measurement intervals**: Shorter → better time resolution but more overhead
- **Integration time**: Longer → better statistics but less temporal detail
- **Coincidence window**: Fixed at ~25 ns for CD48

### Data Quality
- Monitor overflow flags - they indicate counter saturation
- Check singles rates are stable before trusting coincidence data
- Use accidental_analysis.py to verify correlation is real
- Save raw data with data_logger.py for post-processing flexibility

## Common Issues and Solutions

### Import Error
Make sure pycd48 is installed:
```bash
cd ..
pip install -e .
```

### Device Not Found
Try specifying the port manually:
```python
# Linux
with CD48(port='/dev/ttyUSB0') as cd48:
    ...

# Windows
with CD48(port='COM3') as cd48:
    ...
```

### Permission Denied (Linux)
Add your user to the dialout group:
```bash
sudo usermod -a -G dialout $USER
# Then log out and log back in
```

### No Counts / Zero Data
- Check trigger level (try calibrate_trigger.py)
- Verify input signals are connected
- Check impedance setting (50Ω for most detectors)
- Ensure detectors are powered
- Test with LED pulse if available

### Counter Overflow
- Reduce measurement interval
- Use faster polling rate
- Check for very high count rates (>100 kHz)
- Increase threshold to reduce noise

### Unstable Count Rates
- Check detector power supply stability
- Verify detector temperature is stable
- Look for environmental interference (RF, light leaks)
- Use longer integration times for averaging

### Unexpected Coincidence Rates
- Run accidental_analysis.py to check correlation
- Verify detectors are actually seeing correlated events
- Check detector alignment for cosmic rays
- Consider cross-talk between channels

---

## Performance Notes

### Typical Count Rates
- **Cosmic rays (sea level)**: ~1 muon/cm²/min ≈ 150/min for 10×10 cm detector
- **Scintillator noise (typical)**: 100-1000 Hz (depends on threshold)
- **Photomultiplier dark counts**: 100-10,000 Hz (depends on PMT type)
- **Maximum rate**: ~1 MHz per channel (hardware limit)

### Timing Specifications
- **Coincidence window**: ~25 ns (fixed, hardware)
- **USB polling latency**: ~1-50 ms (depends on OS)
- **Minimum interval**: ~100 ms (recommended)
- **Maximum counter value**: 16,777,215 (24-bit for ch 0-6)

### File Sizes (data_logger.py)
- **1 hour @ 1 Hz**: ~500 KB
- **24 hours @ 1 Hz**: ~12 MB
- **1 week @ 1 Hz**: ~85 MB

---

## Further Reading

- [CD48 Product Page](https://www.reddogphysics.com/cd48.html) - Hardware specifications
- [Main README](../README.md) - Complete API documentation
- [Red Dog Physics](https://www.reddogphysics.com/) - Manufacturer website

## Contributing

Have an example you'd like to share? Please submit a pull request!

Good examples to add:
- Muon lifetime measurement analysis
- Quantum entanglement verification
- Multi-detector array calibration
- Advanced statistical analysis
- Real-time plotting with animation
