"""
Continuous Data Collection Example

This example demonstrates continuous monitoring and visualization of
count data over time using matplotlib.
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from pycd48 import CD48


def main() -> None:
    # Connect to CD48
    with CD48() as cd48:
        print("Connected to CD48")
        print(f"Firmware version: {cd48.get_version()}")

        # Setup
        print("\nConfiguring counters...")
        cd48.set_channel(0, A=1, B=0, C=0, D=0)  # Singles A
        cd48.set_channel(1, A=0, B=1, C=0, D=0)  # Singles B
        cd48.set_channel(4, A=1, B=1, C=0, D=0)  # Coincidences AB

        cd48.set_trigger_level(0.5)
        cd48.set_impedance_50ohm()

        print("\nCurrent settings:")
        print(cd48.get_settings(human_readable=True))

        # Collection parameters
        duration = 60  # seconds
        interval = 1  # seconds

        times = []
        counts_A = []
        counts_B = []
        coincidences = []

        print(f"\nCollecting data for {duration} seconds (interval: {interval}s)...")
        print("Time(s)  Ch A    Ch B    A-B Coinc.")
        print("-" * 40)

        start_time = time.time()

        while time.time() - start_time < duration:
            cd48.clear_counts()
            time.sleep(interval)

            data = cd48.get_counts(human_readable=False)

            current_time = time.time() - start_time
            times.append(current_time)
            counts_A.append(data["counts"][0])
            counts_B.append(data["counts"][1])
            coincidences.append(data["counts"][4])

            print(
                f"{current_time:6.1f}  {counts_A[-1]:6d}  {counts_B[-1]:6d}  {coincidences[-1]:6d}"
            )

        # Convert to numpy arrays for analysis
        times = np.array(times)
        counts_A = np.array(counts_A)
        counts_B = np.array(counts_B)
        coincidences = np.array(coincidences)

        # Calculate statistics
        print("\nStatistics:")
        print(f"  Channel A:       {counts_A.mean():8.2f} ± {counts_A.std():6.2f} counts/s")
        print(f"  Channel B:       {counts_B.mean():8.2f} ± {counts_B.std():6.2f} counts/s")
        print(f"  Coincidences AB: {coincidences.mean():8.2f} ± {coincidences.std():6.2f} counts/s")

        # Calculate accidental coincidence rate (assuming uncorrelated sources)
        # Accidental rate = Rate_A * Rate_B * 2 * tau
        # where tau is the coincidence window (~25 ns for CD48)
        tau = 25e-9  # 25 nanoseconds
        accidental_rate = counts_A.mean() * counts_B.mean() * 2 * tau
        true_coincidences = coincidences.mean() - accidental_rate

        print("\nCoincidence Analysis:")
        print(f"  Measured coincidence rate:  {coincidences.mean():8.2f} counts/s")
        print(f"  Expected accidental rate:   {accidental_rate:8.2f} counts/s")
        print(f"  True coincidence rate:      {true_coincidences:8.2f} counts/s")

        # Plot results
        print("\nGenerating plot...")
        plt.figure(figsize=(12, 8))

        # Time series plot
        plt.subplot(2, 1, 1)
        plt.plot(times, counts_A, "o-", label="Channel A", alpha=0.7)
        plt.plot(times, counts_B, "s-", label="Channel B", alpha=0.7)
        plt.plot(times, coincidences, "^-", label="Coincidences AB", alpha=0.7)
        plt.xlabel("Time (s)")
        plt.ylabel("Counts per second")
        plt.title("CD48 Count Rates Over Time")
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Histogram plot
        plt.subplot(2, 1, 2)
        bins = 20
        plt.hist(counts_A, bins=bins, alpha=0.5, label="Channel A")
        plt.hist(counts_B, bins=bins, alpha=0.5, label="Channel B")
        plt.hist(coincidences, bins=bins, alpha=0.5, label="Coincidences AB")
        plt.xlabel("Counts per interval")
        plt.ylabel("Frequency")
        plt.title("Distribution of Count Rates")
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig("cd48_data.png", dpi=150)
        print("Plot saved as 'cd48_data.png'")
        plt.show()


if __name__ == "__main__":
    main()
