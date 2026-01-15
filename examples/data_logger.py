"""
Data Logger Example

This script demonstrates continuous data logging to CSV files for
long-term measurements. Features include:
- Automatic file creation with timestamps
- Configurable measurement intervals
- Real-time data display
- Periodic file flushing for data safety
- Graceful shutdown on Ctrl+C
"""

from typing import Optional
from types import FrameType
import time
import csv
import signal
import sys
from datetime import datetime
from pathlib import Path
from pycd48 import CD48


class DataLogger:
    """CD48 data logger with CSV output"""

    def __init__(self, cd48: CD48, output_dir: str = "data", prefix: str = "cd48") -> None:
        """
        Initialize data logger.

        Parameters:
        -----------
        cd48 : CD48
            Connected CD48 device
        output_dir : str
            Directory for output files
        prefix : str
            Prefix for output filenames
        """
        self.cd48: CD48 = cd48
        self.output_dir: Path = Path(output_dir)
        self.prefix: str = prefix
        self.running: bool = False

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)

        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig: int, frame: Optional[FrameType]) -> None:
        """Handle Ctrl+C gracefully"""
        print("\n\nShutdown signal received. Stopping data collection...")
        self.running = False

    def _create_csv_file(self) -> Path:
        """Create a new CSV file with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{self.prefix}_{timestamp}.csv"

        # Create CSV file with header
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Timestamp",
                    "Elapsed_Time_s",
                    "Ch0_A_singles",
                    "Ch1_B_singles",
                    "Ch2_C_singles",
                    "Ch3_D_singles",
                    "Ch4_AB_coinc",
                    "Ch5_AC_coinc",
                    "Ch6_BC_coinc",
                    "Ch7_ABC_coinc",
                    "Overflow_Flag",
                ]
            )

        return filename

    def log_data(
        self, interval: float = 1.0, duration: Optional[float] = None, display_interval: int = 10
    ) -> None:
        """
        Start logging data to CSV file.

        Parameters:
        -----------
        interval : float
            Time between measurements in seconds
        duration : float, optional
            Total logging duration in seconds (None = run until stopped)
        display_interval : int
            Number of measurements between status updates
        """
        self.running = True

        # Create output file
        filename = self._create_csv_file()
        print(f"Logging to: {filename}")
        print()

        # Print header
        print(f"{'Time':<12} {'Elapsed':<10} {'Ch0':<8} {'Ch1':<8} {'Ch4':<8} {'Status'}")
        print("-" * 60)

        start_time = time.time()
        measurement_count = 0

        try:
            with open(filename, "a", newline="") as f:
                writer = csv.writer(f)

                while self.running:
                    # Check duration limit
                    if duration is not None:
                        if time.time() - start_time >= duration:
                            print("\nDuration limit reached.")
                            break

                    # Clear counters and measure
                    self.cd48.clear_counts()
                    time.sleep(interval)

                    # Get data
                    data = self.cd48.get_counts(human_readable=False)
                    counts = data["counts"]
                    overflow = data["overflow"]

                    # Record timestamp
                    now = datetime.now()
                    elapsed = time.time() - start_time

                    # Write to CSV
                    writer.writerow(
                        [
                            now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # Timestamp
                            f"{elapsed:.3f}",  # Elapsed time
                            counts[0],  # Ch0
                            counts[1],  # Ch1
                            counts[2],  # Ch2
                            counts[3],  # Ch3
                            counts[4],  # Ch4
                            counts[5],  # Ch5
                            counts[6],  # Ch6
                            counts[7],  # Ch7
                            overflow,  # Overflow flag
                        ]
                    )

                    measurement_count += 1

                    # Flush to disk periodically for data safety
                    if measurement_count % 10 == 0:
                        f.flush()

                    # Display status
                    if measurement_count % display_interval == 0 or measurement_count == 1:
                        status = "OK"
                        if overflow:
                            status = f"OVERFLOW:0x{overflow:02X}"

                        print(
                            f"{now.strftime('%H:%M:%S'):<12} "
                            f"{elapsed:>8.1f}s  "
                            f"{counts[0]:>7d} "
                            f"{counts[1]:>7d} "
                            f"{counts[4]:>7d} "
                            f"{status}"
                        )

        except Exception as e:
            print(f"\nError during logging: {e}")
        finally:
            print()
            print("=" * 60)
            print(f"Data logging completed")
            print(f"  Total measurements: {measurement_count}")
            print(f"  Total time: {time.time() - start_time:.1f}s")
            print(f"  Output file: {filename}")
            print(f"  File size: {filename.stat().st_size / 1024:.1f} KB")
            print("=" * 60)


def main() -> None:
    print("=" * 60)
    print("CD48 Data Logger")
    print("=" * 60)
    print()

    # Configuration
    INTERVAL = 1.0  # seconds between measurements
    DURATION = None  # None = run until Ctrl+C, or set duration in seconds
    DISPLAY_INTERVAL = 10  # Show status every N measurements

    print("Configuration:")
    print(f"  Measurement interval: {INTERVAL}s")
    if DURATION:
        print(f"  Duration: {DURATION}s ({DURATION/60:.1f} minutes)")
    else:
        print(f"  Duration: Continuous (press Ctrl+C to stop)")
    print(f"  Display update: Every {DISPLAY_INTERVAL} measurements")
    print()

    with CD48() as cd48:
        print(f"Connected to CD48 - Firmware: {cd48.get_version()}")
        print()

        # Configure channels
        print("Configuring channels...")
        cd48.set_channel(0, A=1, B=0, C=0, D=0)  # A singles
        cd48.set_channel(1, A=0, B=1, C=0, D=0)  # B singles
        cd48.set_channel(2, A=0, B=0, C=1, D=0)  # C singles
        cd48.set_channel(3, A=0, B=0, C=0, D=1)  # D singles
        cd48.set_channel(4, A=1, B=1, C=0, D=0)  # A-B coincidence
        cd48.set_channel(5, A=1, B=0, C=1, D=0)  # A-C coincidence
        cd48.set_channel(6, A=0, B=1, C=1, D=0)  # B-C coincidence
        cd48.set_channel(7, A=1, B=1, C=1, D=0)  # A-B-C triple

        # Set trigger level
        trigger_level = 0.5
        print(f"Setting trigger level to {trigger_level}V")
        cd48.set_trigger_level(trigger_level)

        # Set impedance
        print("Setting 50 Ohm input impedance")
        cd48.set_impedance_50ohm()
        print()

        # Create logger and start
        logger = DataLogger(cd48, output_dir="data", prefix="cd48_log")

        print("Starting data collection...")
        print("Press Ctrl+C to stop")
        print()

        logger.log_data(interval=INTERVAL, duration=DURATION, display_interval=DISPLAY_INTERVAL)


if __name__ == "__main__":
    main()
