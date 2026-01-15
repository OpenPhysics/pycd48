"""
Cosmic Ray Telescope Example

This example demonstrates configuration for a cosmic ray muon detector
with a vertical telescope arrangement of scintillation detectors.

Typical setup:
- Detectors A and B: Top and bottom of telescope (vertical alignment)
- Detector C: Optional middle detector
- Detector D: Side detector for background monitoring

The example measures:
- Singles rates on each detector
- Two-fold coincidences (A-B) for vertical muons
- Three-fold coincidences (A-B-C) for higher selectivity
- Background on detector D
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pycd48 import CD48


def main():
    print("=" * 60)
    print("CD48 Cosmic Ray Muon Telescope")
    print("=" * 60)
    print()

    # Connect to CD48
    with CD48() as cd48:
        print(f"Connected to CD48 - Firmware: {cd48.get_version()}")
        print()

        # Configuration for cosmic ray telescope
        print("Configuring telescope...")
        print("  Channel 0: Detector A (top)")
        print("  Channel 1: Detector B (bottom)")
        print("  Channel 2: Detector C (middle)")
        print("  Channel 3: Detector D (background)")
        print("  Channel 4: A-B coincidence (2-fold)")
        print("  Channel 5: A-B-C coincidence (3-fold)")
        print("  Channel 6: A-C coincidence")
        print("  Channel 7: B-C coincidence")
        print()

        # Configure channels
        cd48.set_channel(0, A=1, B=0, C=0, D=0)  # Singles A (top)
        cd48.set_channel(1, A=0, B=1, C=0, D=0)  # Singles B (bottom)
        cd48.set_channel(2, A=0, B=0, C=1, D=0)  # Singles C (middle)
        cd48.set_channel(3, A=0, B=0, C=0, D=1)  # Singles D (background)
        cd48.set_channel(4, A=1, B=1, C=0, D=0)  # A-B 2-fold
        cd48.set_channel(5, A=1, B=1, C=1, D=0)  # A-B-C 3-fold
        cd48.set_channel(6, A=1, B=0, C=1, D=0)  # A-C
        cd48.set_channel(7, A=0, B=1, C=1, D=0)  # B-C

        # Set trigger level optimized for scintillation detectors
        trigger_voltage = 0.3  # Adjust based on your PMTs/SiPMs
        print(f"Setting trigger level to {trigger_voltage}V")
        cd48.set_trigger_level(trigger_voltage)

        # Use 50 Ohm impedance for good signal integrity
        print("Setting 50 Ohm input impedance")
        cd48.set_impedance_50ohm()
        print()

        # Measurement parameters
        interval = 5  # seconds per measurement
        total_duration = 300  # 5 minutes total
        num_measurements = total_duration // interval

        # Data storage
        timestamps = []
        singles_A = []
        singles_B = []
        singles_C = []
        singles_D = []
        coinc_AB = []
        coinc_ABC = []
        coinc_AC = []
        coinc_BC = []

        print(f"Starting {total_duration}s measurement ({interval}s intervals)...")
        print()
        print(f"{'Time':<12} {'A':<8} {'B':<8} {'C':<8} {'D':<8} {'A-B':<8} {'A-B-C':<8}")
        print("-" * 68)

        start_time = time.time()

        for i in range(num_measurements):
            cd48.clear_counts()
            time.sleep(interval)

            data = cd48.get_counts(human_readable=False)
            counts = data['counts']

            # Store data
            elapsed = time.time() - start_time
            timestamps.append(elapsed)
            singles_A.append(counts[0] / interval)  # Convert to rate (Hz)
            singles_B.append(counts[1] / interval)
            singles_C.append(counts[2] / interval)
            singles_D.append(counts[3] / interval)
            coinc_AB.append(counts[4] / interval)
            coinc_ABC.append(counts[5] / interval)
            coinc_AC.append(counts[6] / interval)
            coinc_BC.append(counts[7] / interval)

            # Display current measurement
            print(f"{elapsed:>6.0f}s     "
                  f"{singles_A[-1]:>7.1f} "
                  f"{singles_B[-1]:>7.1f} "
                  f"{singles_C[-1]:>7.1f} "
                  f"{singles_D[-1]:>7.1f} "
                  f"{coinc_AB[-1]:>7.1f} "
                  f"{coinc_ABC[-1]:>7.1f}")

        # Convert to numpy arrays for analysis
        timestamps = np.array(timestamps)
        singles_A = np.array(singles_A)
        singles_B = np.array(singles_B)
        singles_C = np.array(singles_C)
        singles_D = np.array(singles_D)
        coinc_AB = np.array(coinc_AB)
        coinc_ABC = np.array(coinc_ABC)
        coinc_AC = np.array(coinc_AC)
        coinc_BC = np.array(coinc_BC)

        print()
        print("=" * 68)
        print("MEASUREMENT SUMMARY")
        print("=" * 68)
        print()

        # Calculate statistics
        print("Average Count Rates (Hz):")
        print(f"  Detector A (top):        {singles_A.mean():8.2f} ± {singles_A.std():6.2f}")
        print(f"  Detector B (bottom):     {singles_B.mean():8.2f} ± {singles_B.std():6.2f}")
        print(f"  Detector C (middle):     {singles_C.mean():8.2f} ± {singles_C.std():6.2f}")
        print(f"  Detector D (background): {singles_D.mean():8.2f} ± {singles_D.std():6.2f}")
        print()
        print("Coincidence Rates (Hz):")
        print(f"  A-B (2-fold):            {coinc_AB.mean():8.2f} ± {coinc_AB.std():6.2f}")
        print(f"  A-B-C (3-fold):          {coinc_ABC.mean():8.2f} ± {coinc_ABC.std():6.2f}")
        print(f"  A-C:                     {coinc_AC.mean():8.2f} ± {coinc_AC.std():6.2f}")
        print(f"  B-C:                     {coinc_BC.mean():8.2f} ± {coinc_BC.std():6.2f}")
        print()

        # Accidental coincidence analysis
        tau = 10e-9  # 10 ns coincidence window
        accidental_AB = 2 * tau * singles_A.mean() * singles_B.mean()
        accidental_ABC = 3 * tau * singles_A.mean() * singles_B.mean() * singles_C.mean()

        true_coinc_AB = coinc_AB.mean() - accidental_AB
        true_coinc_ABC = coinc_ABC.mean() - accidental_ABC

        print("Accidental Coincidence Analysis:")
        print(f"  Expected accidental A-B:  {accidental_AB:8.2f} Hz")
        print(f"  True A-B coincidences:    {true_coinc_AB:8.2f} Hz")
        print(f"  Expected accidental A-B-C:{accidental_ABC:8.2f} Hz")
        print(f"  True A-B-C coincidences:  {true_coinc_ABC:8.2f} Hz")
        print()

        # Telescope efficiency (assuming top-to-bottom geometry)
        if singles_A.mean() > 0:
            efficiency_2fold = (coinc_AB.mean() / singles_A.mean()) * 100
            efficiency_3fold = (coinc_ABC.mean() / singles_A.mean()) * 100
            print("Telescope Efficiency:")
            print(f"  2-fold (A-B):   {efficiency_2fold:6.2f}%")
            print(f"  3-fold (A-B-C): {efficiency_3fold:6.2f}%")
            print()

        # Estimate muon flux (rough calculation)
        # Typical detector area: ~100 cm² = 0.01 m²
        detector_area = 0.01  # m²
        muon_flux = true_coinc_AB / detector_area
        print(f"Estimated Muon Flux: {muon_flux:.1f} muons/(m²·s)")
        print(f"  (Typical sea level: ~100 muons/(m²·s))")
        print()

        # Create visualization
        print("Generating plots...")
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Plot 1: Singles rates over time
        ax1 = axes[0, 0]
        ax1.plot(timestamps / 60, singles_A, 'o-', label='Detector A (top)', alpha=0.7)
        ax1.plot(timestamps / 60, singles_B, 's-', label='Detector B (bottom)', alpha=0.7)
        ax1.plot(timestamps / 60, singles_C, '^-', label='Detector C (middle)', alpha=0.7)
        ax1.plot(timestamps / 60, singles_D, 'd-', label='Detector D (background)', alpha=0.7)
        ax1.set_xlabel('Time (minutes)')
        ax1.set_ylabel('Count Rate (Hz)')
        ax1.set_title('Singles Rates Over Time')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Coincidence rates over time
        ax2 = axes[0, 1]
        ax2.plot(timestamps / 60, coinc_AB, 'o-', label='A-B (2-fold)', alpha=0.7)
        ax2.plot(timestamps / 60, coinc_ABC, 's-', label='A-B-C (3-fold)', alpha=0.7)
        ax2.axhline(y=coinc_AB.mean(), color='blue', linestyle='--', alpha=0.5, label='A-B mean')
        ax2.axhline(y=coinc_ABC.mean(), color='orange', linestyle='--', alpha=0.5, label='A-B-C mean')
        ax2.set_xlabel('Time (minutes)')
        ax2.set_ylabel('Coincidence Rate (Hz)')
        ax2.set_title('Coincidence Rates Over Time')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot 3: Distribution of coincidence rates
        ax3 = axes[1, 0]
        ax3.hist(coinc_AB, bins=20, alpha=0.6, label='A-B (2-fold)', edgecolor='black')
        ax3.hist(coinc_ABC, bins=20, alpha=0.6, label='A-B-C (3-fold)', edgecolor='black')
        ax3.set_xlabel('Coincidence Rate (Hz)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Distribution of Coincidence Rates')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Plot 4: Correlation plot
        ax4 = axes[1, 1]
        ax4.scatter(singles_A, coinc_AB, alpha=0.6, s=50)
        ax4.set_xlabel('Detector A Rate (Hz)')
        ax4.set_ylabel('A-B Coincidence Rate (Hz)')
        ax4.set_title('Correlation: Singles vs Coincidences')
        ax4.grid(True, alpha=0.3)

        # Add correlation coefficient
        if len(singles_A) > 1:
            correlation = np.corrcoef(singles_A, coinc_AB)[0, 1]
            ax4.text(0.05, 0.95, f'R = {correlation:.3f}',
                    transform=ax4.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        # Save plot with timestamp
        filename = f'cosmic_ray_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=150)
        print(f"Plot saved as '{filename}'")
        plt.show()


if __name__ == "__main__":
    main()
