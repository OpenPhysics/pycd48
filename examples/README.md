# pycd48 Examples

Start with the notebook: `jupyter lab pycd48_tutorial.ipynb` (install Jupyter separately). It walks through connecting, counting, plotting, accidental-coincidence analysis, DAC control, overflow detection and logging.

Each script has a docstring with details and runs with `python <script>.py`. Pass `CD48(port='/dev/ttyUSB0')` (or `'COM3'` on Windows) if auto-detection fails.

| Script | Purpose |
|---|---|
| `device_info.py` | Connect, print firmware version and settings; good first check |
| `simple_counting.py` | Basic counting and coincidence measurement |
| `continuous_collection.py` | Continuous data collection over time |
| `cosmic_ray_telescope.py` | Coincidence-based cosmic ray telescope setup |
| `calibrate_trigger.py` | Find a good trigger level |
| `data_logger.py` | Log counts to CSV/JSON |
| `accidental_analysis.py` | Estimate accidental coincidence rates |
| `realtime_monitor.py` | Live monitoring using repeat mode |
| `voltage_sweep.py` | Sweep the DAC output voltage |
| `overflow_demo.py` | Detect and handle counter overflow |
| `run_yaml_experiment.py` | Run an experiment from a YAML config (see [configs/README.md](configs/README.md)) |

## Troubleshooting
- **Import error:** install the package from the repo root with `pip install -e .`.
- **Permission denied (Linux):** `sudo usermod -a -G dialout $USER`, then log out and back in.
- **No counts:** check the trigger level (`calibrate_trigger.py`), the input cabling, detector power and the impedance setting (50 Ω for most detectors).
- **Counter overflow:** shorten the measurement interval or raise the threshold.
- **Unexpected coincidence rates:** run `accidental_analysis.py`, and check alignment and channel cross-talk.
