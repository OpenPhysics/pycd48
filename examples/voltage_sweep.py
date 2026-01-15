"""
Voltage Sweep Example using DAC Output

This example demonstrates using the CD48's DAC output to control
external equipment while measuring coincidences. This is useful for:

- Voltage-dependent measurements (e.g., PMT high voltage optimization)
- Automated equipment control
- Feedback loops for experiment optimization
- Scanning experiments

Example use case: Finding optimal PMT operating voltage by sweeping
the high voltage and measuring count rates.
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from pycd48 import CD48


def sweep_voltage(cd48, voltage_range, measurement_time=5):
    """
    Sweep DAC voltage and measure count rates.

    Parameters:
    -----------
    cd48 : CD48
        Connected CD48 device
    voltage_range : array-like
        Voltages to sweep (0-4.08V)
    measurement_time : float
        Integration time per voltage (seconds)

    Returns:
    --------
    results : dict
        Measurement results at each voltage
    """
    voltages = []
    counts_A = []
    counts_B = []
    coincidences = []

    print(f"Sweeping {len(voltage_range)} voltage points...")
    print(f"Integration time: {measurement_time}s per point")
    print()
    print(f"{'Voltage (V)':<12} {'Ch A':<10} {'Ch B':<10} {'Coinc AB':<10}")
    print("-" * 50)

    for voltage in voltage_range:
        # Set DAC output voltage
        cd48.set_dac_voltage(voltage)
        time.sleep(0.5)  # Allow external equipment to settle

        # Clear counters and measure
        cd48.clear_counts()
        time.sleep(measurement_time)

        # Read results
        data = cd48.get_counts(human_readable=False)

        # Store data
        voltages.append(voltage)
        counts_A.append(data['counts'][0])
        counts_B.append(data['counts'][1])
        coincidences.append(data['counts'][4])

        # Display progress
        print(f"{voltage:>6.2f}       {data['counts'][0]:<10} "
              f"{data['counts'][1]:<10} {data['counts'][4]:<10}")

    return {
        'voltages': np.array(voltages),
        'counts_A': np.array(counts_A),
        'counts_B': np.array(counts_B),
        'coincidences': np.array(coincidences)
    }


def main():
    print("=" * 60)
    print("CD48 Voltage Sweep Experiment")
    print("=" * 60)
    print()
    print("This example sweeps the DAC output voltage from 0-4V")
    print("while measuring count rates. Connect the DAC output")
    print("to your external equipment (e.g., PMT power supply).")
    print()

    with CD48() as cd48:
        print(f"Connected to CD48 - Firmware: {cd48.get_version()}")
        print()

        # Configure channels
        print("Configuring channels...")
        cd48.set_channel(0, A=1, B=0, C=0, D=0)  # A singles
        cd48.set_channel(1, A=0, B=1, C=0, D=0)  # B singles
        cd48.set_channel(4, A=1, B=1, C=0, D=0)  # A-B coincidences

        cd48.set_trigger_level(0.5)
        cd48.set_impedance_50ohm()
        print()

        # Define voltage sweep parameters
        v_min = 0.0
        v_max = 4.0
        v_steps = 20
        measurement_time = 3  # seconds per point

        voltage_range = np.linspace(v_min, v_max, v_steps)

        print(f"Sweep parameters:")
        print(f"  Voltage range: {v_min}V to {v_max}V")
        print(f"  Steps: {v_steps}")
        print(f"  Time per point: {measurement_time}s")
        print(f"  Total time: ~{v_steps * measurement_time:.0f}s")
        print()

        input("Press Enter to start sweep...")
        print()

        # Perform sweep
        results = sweep_voltage(cd48, voltage_range, measurement_time)

        # Set DAC back to 0V when done
        print("\nSweep complete. Setting DAC to 0V...")
        cd48.set_dac_voltage(0.0)

        # Calculate rates (counts per second)
        rate_A = results['counts_A'] / measurement_time
        rate_B = results['counts_B'] / measurement_time
        rate_coinc = results['coincidences'] / measurement_time

        # Find optimal voltage (maximum coincidence rate)
        max_idx = np.argmax(rate_coinc)
        optimal_voltage = results['voltages'][max_idx]
        max_coinc_rate = rate_coinc[max_idx]

        print()
        print("=" * 60)
        print("ANALYSIS")
        print("=" * 60)
        print()
        print(f"Optimal voltage: {optimal_voltage:.2f}V")
        print(f"Maximum coincidence rate: {max_coinc_rate:.2f} Hz")
        print()
        print("Note: The 'optimal' voltage depends on your specific")
        print("experimental goals (e.g., maximum S/N ratio vs maximum rate)")

        # Generate plots
        print("\nGenerating plots...")
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Plot 1: Count rates vs voltage
        ax1 = axes[0, 0]
        ax1.plot(results['voltages'], rate_A, 'o-', label='Channel A', linewidth=2)
        ax1.plot(results['voltages'], rate_B, 's-', label='Channel B', linewidth=2)
        ax1.plot(results['voltages'], rate_coinc, '^-', label='A-B Coinc', linewidth=2)
        ax1.axvline(optimal_voltage, color='red', linestyle='--', alpha=0.5,
                   label=f'Optimal: {optimal_voltage:.2f}V')
        ax1.set_xlabel('DAC Voltage (V)', fontsize=12)
        ax1.set_ylabel('Count Rate (Hz)', fontsize=12)
        ax1.set_title('Count Rates vs DAC Voltage', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Coincidence rate (zoomed)
        ax2 = axes[0, 1]
        ax2.plot(results['voltages'], rate_coinc, 'o-', linewidth=2, markersize=8,
                color='green')
        ax2.axvline(optimal_voltage, color='red', linestyle='--', alpha=0.5)
        ax2.plot(optimal_voltage, max_coinc_rate, 'r*', markersize=20,
                label=f'Max: {max_coinc_rate:.1f} Hz')
        ax2.set_xlabel('DAC Voltage (V)', fontsize=12)
        ax2.set_ylabel('Coincidence Rate (Hz)', fontsize=12)
        ax2.set_title('Coincidence Rate Optimization', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot 3: Signal-to-noise estimation
        ax3 = axes[1, 0]
        # Estimate S/N as coincidences / sqrt(singles)
        # (simplified - real S/N depends on your specific application)
        sn_ratio = rate_coinc / np.sqrt(rate_A * rate_B + 1)
        max_sn_idx = np.argmax(sn_ratio)

        ax3.plot(results['voltages'], sn_ratio, 'o-', linewidth=2, color='purple')
        ax3.axvline(results['voltages'][max_sn_idx], color='red',
                   linestyle='--', alpha=0.5,
                   label=f'Best S/N: {results["voltages"][max_sn_idx]:.2f}V')
        ax3.set_xlabel('DAC Voltage (V)', fontsize=12)
        ax3.set_ylabel('Figure of Merit (a.u.)', fontsize=12)
        ax3.set_title('Signal-to-Noise Estimate', fontsize=14, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Plot 4: Total counts
        ax4 = axes[1, 1]
        ax4.bar(results['voltages'], results['coincidences'],
               width=0.15, alpha=0.7, edgecolor='black')
        ax4.set_xlabel('DAC Voltage (V)', fontsize=12)
        ax4.set_ylabel('Total Coincidences', fontsize=12)
        ax4.set_title(f'Total Coincidences ({measurement_time}s integration)',
                     fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig('voltage_sweep.png', dpi=150)
        print("Plot saved as 'voltage_sweep.png'")
        plt.show()

        print()
        print("=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        print()
        print(f"For maximum coincidence rate: {optimal_voltage:.2f}V")
        print(f"For best S/N ratio: {results['voltages'][max_sn_idx]:.2f}V")
        print()
        print("Choose based on your experimental requirements:")
        print("  - Use max rate voltage for high statistics")
        print("  - Use best S/N voltage for low background")


if __name__ == "__main__":
    main()
