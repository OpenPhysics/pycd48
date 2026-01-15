"""
Trigger Level Calibration Example

This script helps you find the optimal trigger threshold for your detectors
by scanning through different voltage levels and measuring the count rate.

This is useful for:
- Finding the noise threshold of your detectors
- Optimizing signal-to-noise ratio
- Setting consistent trigger levels across multiple detectors
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from pycd48 import CD48


def scan_trigger_levels(cd48, channel_config, voltage_range, measurement_time=5):
    """
    Scan trigger levels and measure count rates.

    Parameters:
    -----------
    cd48 : CD48
        Connected CD48 device
    channel_config : dict
        Channel configuration {channel: (A, B, C, D)}
    voltage_range : array-like
        Trigger voltages to scan
    measurement_time : float
        Integration time per voltage (seconds)

    Returns:
    --------
    results : dict
        Dictionary with voltage as key and count rates as value
    """
    results = {i: [] for i in channel_config.keys()}
    voltages = []

    print(f"Scanning {len(voltage_range)} voltage levels...")
    print(f"Integration time: {measurement_time}s per level")
    print()
    print(f"{'Voltage (V)':<12} ", end='')
    for ch in sorted(channel_config.keys()):
        print(f"Ch{ch} (Hz)  ", end='')
    print()
    print("-" * 60)

    for voltage in voltage_range:
        # Set trigger level
        cd48.set_trigger_level(voltage)
        time.sleep(0.2)  # Allow hardware to settle

        # Clear and measure
        cd48.clear_counts()
        time.sleep(measurement_time)

        data = cd48.get_counts(human_readable=False)
        counts = data['counts']

        # Store results
        voltages.append(voltage)
        print(f"{voltage:>6.3f}       ", end='')

        for ch in sorted(channel_config.keys()):
            rate = counts[ch] / measurement_time
            results[ch].append(rate)
            print(f"{rate:>8.1f} ", end='')
        print()

    return voltages, results


def main():
    print("=" * 60)
    print("CD48 Trigger Level Calibration")
    print("=" * 60)
    print()

    with CD48() as cd48:
        print(f"Connected to CD48 - Firmware: {cd48.get_version()}")
        print()

        # Configuration
        print("Configuring channels for singles counting...")
        channel_config = {
            0: (1, 0, 0, 0),  # Channel A
            1: (0, 1, 0, 0),  # Channel B
            2: (0, 0, 1, 0),  # Channel C
            3: (0, 0, 0, 1),  # Channel D
        }

        for ch, (A, B, C, D) in channel_config.items():
            cd48.set_channel(ch, A=A, B=B, C=C, D=D)

        cd48.set_impedance_50ohm()
        print()

        # Define voltage scan range
        # Scan from high to low to avoid triggering on noise initially
        voltage_min = 0.1   # V
        voltage_max = 2.0   # V
        voltage_step = 0.1  # V

        voltage_range = np.arange(voltage_max, voltage_min - voltage_step, -voltage_step)
        measurement_time = 3  # seconds per point

        print(f"Scanning range: {voltage_min}V to {voltage_max}V")
        print(f"Step size: {voltage_step}V")
        print(f"Total scan time: ~{len(voltage_range) * measurement_time:.0f} seconds")
        print()

        input("Connect your detectors and press Enter to start scan...")
        print()

        # Perform scan
        voltages, results = scan_trigger_levels(
            cd48, channel_config, voltage_range, measurement_time
        )

        # Convert to numpy arrays
        voltages = np.array(voltages)
        for ch in results:
            results[ch] = np.array(results[ch])

        print()
        print("=" * 60)
        print("ANALYSIS")
        print("=" * 60)
        print()

        # Find optimal thresholds
        optimal_thresholds = {}

        for ch in sorted(channel_config.keys()):
            rates = results[ch]

            # Find where rate starts to plateau (derivative analysis)
            if len(rates) > 3:
                # Calculate derivative (rate of change)
                derivative = np.gradient(rates, voltages)

                # Find the "knee" - where derivative is minimum (most negative)
                # This is where we transition from noise to signal
                knee_idx = np.argmin(derivative)
                optimal_voltage = voltages[knee_idx]
                optimal_thresholds[ch] = optimal_voltage

                print(f"Channel {ch}:")
                print(f"  Suggested threshold: {optimal_voltage:.3f}V")
                print(f"  Count rate at threshold: {rates[knee_idx]:.1f} Hz")
                print(f"  Maximum rate: {rates.max():.1f} Hz @ {voltages[np.argmax(rates)]:.3f}V")
                print(f"  Minimum rate: {rates.min():.1f} Hz @ {voltages[np.argmin(rates)]:.3f}V")
                print()

        # Plot results
        print("Generating plots...")
        fig, axes = plt.subplots(2, 1, figsize=(10, 10))

        # Plot 1: Count rate vs trigger voltage
        ax1 = axes[0]
        channel_names = ['Channel A', 'Channel B', 'Channel C', 'Channel D']
        colors = ['blue', 'orange', 'green', 'red']

        for ch in sorted(channel_config.keys()):
            ax1.plot(voltages, results[ch], 'o-', label=channel_names[ch],
                    color=colors[ch], alpha=0.7, linewidth=2, markersize=6)

            # Mark optimal threshold
            if ch in optimal_thresholds:
                opt_v = optimal_thresholds[ch]
                opt_idx = np.argmin(np.abs(voltages - opt_v))
                ax1.axvline(x=opt_v, color=colors[ch], linestyle='--', alpha=0.3)
                ax1.plot(opt_v, results[ch][opt_idx], '*',
                        color=colors[ch], markersize=15,
                        markeredgecolor='black', markeredgewidth=1)

        ax1.set_xlabel('Trigger Voltage (V)', fontsize=12)
        ax1.set_ylabel('Count Rate (Hz)', fontsize=12)
        ax1.set_title('Count Rate vs Trigger Threshold', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')  # Log scale often shows noise floor better

        # Plot 2: Normalized rates (easier to compare channels)
        ax2 = axes[1]
        for ch in sorted(channel_config.keys()):
            # Normalize to maximum
            normalized = results[ch] / results[ch].max() if results[ch].max() > 0 else results[ch]
            ax2.plot(voltages, normalized, 'o-', label=channel_names[ch],
                    color=colors[ch], alpha=0.7, linewidth=2, markersize=6)

            # Mark optimal threshold
            if ch in optimal_thresholds:
                opt_v = optimal_thresholds[ch]
                opt_idx = np.argmin(np.abs(voltages - opt_v))
                ax2.axvline(x=opt_v, color=colors[ch], linestyle='--', alpha=0.3)

        ax2.set_xlabel('Trigger Voltage (V)', fontsize=12)
        ax2.set_ylabel('Normalized Count Rate', fontsize=12)
        ax2.set_title('Normalized Count Rate vs Trigger Threshold', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim([0, 1.1])

        plt.tight_layout()
        plt.savefig('trigger_calibration.png', dpi=150)
        print("Plot saved as 'trigger_calibration.png'")
        plt.show()

        # Recommendations
        print()
        print("=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        print()
        print("Based on the scan, consider these trigger levels:")
        print()

        for ch in sorted(optimal_thresholds.keys()):
            print(f"  cd48.set_trigger_level({optimal_thresholds[ch]:.3f})  # Channel {ch}")

        print()
        print("Note: These are automatic suggestions. You should:")
        print("  1. Review the plots to understand the noise characteristics")
        print("  2. Consider your signal amplitude and desired sensitivity")
        print("  3. Test the suggested values with your actual measurements")
        print("  4. Adjust based on your specific requirements")


if __name__ == "__main__":
    main()
