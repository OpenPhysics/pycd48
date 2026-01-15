"""
Accidental Coincidence Analysis Example

This script performs detailed analysis of coincidence data to separate
true coincidences from random (accidental) coincidences.

Background:
-----------
When counting coincidences between uncorrelated sources, random coincidences
can occur purely by chance. The expected accidental coincidence rate is:

    R_acc = 2 × τ × R_A × R_B

where:
    τ = coincidence window (~25 ns for CD48)
    R_A, R_B = singles rates on channels A and B

This example demonstrates:
- Measuring singles and coincidence rates
- Calculating expected accidental rate
- Determining true coincidence rate
- Statistical significance testing
- Visualization of results
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pycd48 import CD48


def measure_rates(cd48, num_samples=30, interval=2.0):
    """
    Measure singles and coincidence rates over multiple samples.

    Parameters:
    -----------
    cd48 : CD48
        Connected CD48 device
    num_samples : int
        Number of measurements to take
    interval : float
        Integration time per measurement (seconds)

    Returns:
    --------
    data : dict
        Dictionary containing arrays of measured rates
    """
    print(f"Collecting {num_samples} measurements ({interval}s each)...")
    print()

    rate_A = []
    rate_B = []
    rate_C = []
    coinc_AB = []
    coinc_AC = []
    coinc_BC = []
    coinc_ABC = []

    print(f"{'Sample':<8} {'A (Hz)':<10} {'B (Hz)':<10} {'A-B (Hz)':<10}")
    print("-" * 45)

    for i in range(num_samples):
        cd48.clear_counts()
        time.sleep(interval)

        data = cd48.get_counts(human_readable=False)
        counts = data['counts']

        # Convert to rates (Hz)
        rate_A.append(counts[0] / interval)
        rate_B.append(counts[1] / interval)
        rate_C.append(counts[2] / interval)
        coinc_AB.append(counts[4] / interval)
        coinc_AC.append(counts[5] / interval)
        coinc_BC.append(counts[6] / interval)
        coinc_ABC.append(counts[7] / interval)

        if (i + 1) % 5 == 0 or i == 0:
            print(f"{i+1:<8} {rate_A[-1]:<10.2f} {rate_B[-1]:<10.2f} {coinc_AB[-1]:<10.2f}")

    print()

    return {
        'rate_A': np.array(rate_A),
        'rate_B': np.array(rate_B),
        'rate_C': np.array(rate_C),
        'coinc_AB': np.array(coinc_AB),
        'coinc_AC': np.array(coinc_AC),
        'coinc_BC': np.array(coinc_BC),
        'coinc_ABC': np.array(coinc_ABC),
    }


def analyze_coincidences(data, tau=25e-9):
    """
    Analyze coincidence data to separate true from accidental coincidences.

    Parameters:
    -----------
    data : dict
        Measurement data from measure_rates()
    tau : float
        Coincidence window in seconds (default: 25 ns)

    Returns:
    --------
    results : dict
        Analysis results
    """
    results = {}

    # A-B coincidences
    mean_A = data['rate_A'].mean()
    mean_B = data['rate_B'].mean()
    mean_coinc_AB = data['coinc_AB'].mean()

    # Calculate accidental rate
    accidental_AB = 2 * tau * mean_A * mean_B

    # True coincidence rate
    true_coinc_AB = mean_coinc_AB - accidental_AB

    # Statistical uncertainty (Poisson statistics)
    # For Poisson: σ = √N, so σ_rate = √N / t
    std_coinc_AB = data['coinc_AB'].std()

    # Significance of true coincidences
    if std_coinc_AB > 0:
        significance = true_coinc_AB / std_coinc_AB
    else:
        significance = 0

    results['AB'] = {
        'mean_A': mean_A,
        'mean_B': mean_B,
        'mean_coinc': mean_coinc_AB,
        'std_coinc': std_coinc_AB,
        'accidental': accidental_AB,
        'true_coinc': true_coinc_AB,
        'significance': significance,
        'accidental_fraction': accidental_AB / mean_coinc_AB if mean_coinc_AB > 0 else 0
    }

    # A-C coincidences
    mean_C = data['rate_C'].mean()
    mean_coinc_AC = data['coinc_AC'].mean()
    accidental_AC = 2 * tau * mean_A * mean_C
    true_coinc_AC = mean_coinc_AC - accidental_AC

    results['AC'] = {
        'mean_A': mean_A,
        'mean_C': mean_C,
        'mean_coinc': mean_coinc_AC,
        'std_coinc': data['coinc_AC'].std(),
        'accidental': accidental_AC,
        'true_coinc': true_coinc_AC,
        'accidental_fraction': accidental_AC / mean_coinc_AC if mean_coinc_AC > 0 else 0
    }

    # A-B-C triple coincidences (simplified approximation)
    mean_coinc_ABC = data['coinc_ABC'].mean()
    # For triple coincidences, accidental rate is more complex
    # Approximation: R_acc ≈ 3 × τ × R_A × R_B × R_C
    accidental_ABC = 3 * tau * mean_A * mean_B * mean_C
    true_coinc_ABC = mean_coinc_ABC - accidental_ABC

    results['ABC'] = {
        'mean_coinc': mean_coinc_ABC,
        'std_coinc': data['coinc_ABC'].std(),
        'accidental': accidental_ABC,
        'true_coinc': true_coinc_ABC,
        'accidental_fraction': accidental_ABC / mean_coinc_ABC if mean_coinc_ABC > 0 else 0
    }

    return results


def print_results(results):
    """Print analysis results in a formatted table."""
    print("=" * 70)
    print("COINCIDENCE ANALYSIS RESULTS")
    print("=" * 70)
    print()

    # A-B Coincidences
    print("A-B Coincidences:")
    print(f"  Singles rate A:           {results['AB']['mean_A']:>10.2f} Hz")
    print(f"  Singles rate B:           {results['AB']['mean_B']:>10.2f} Hz")
    print(f"  Measured coincidences:    {results['AB']['mean_coinc']:>10.2f} Hz")
    print(f"  Expected accidentals:     {results['AB']['accidental']:>10.2f} Hz")
    print(f"  True coincidences:        {results['AB']['true_coinc']:>10.2f} Hz")
    print(f"  Accidental fraction:      {results['AB']['accidental_fraction']*100:>10.2f} %")
    print(f"  Statistical significance: {results['AB']['significance']:>10.2f} σ")
    print()

    # A-C Coincidences
    print("A-C Coincidences:")
    print(f"  Singles rate A:           {results['AC']['mean_A']:>10.2f} Hz")
    print(f"  Singles rate C:           {results['AC']['mean_C']:>10.2f} Hz")
    print(f"  Measured coincidences:    {results['AC']['mean_coinc']:>10.2f} Hz")
    print(f"  Expected accidentals:     {results['AC']['accidental']:>10.2f} Hz")
    print(f"  True coincidences:        {results['AC']['true_coinc']:>10.2f} Hz")
    print(f"  Accidental fraction:      {results['AC']['accidental_fraction']*100:>10.2f} %")
    print()

    # A-B-C Triple Coincidences
    print("A-B-C Triple Coincidences:")
    print(f"  Measured coincidences:    {results['ABC']['mean_coinc']:>10.2f} Hz")
    print(f"  Expected accidentals:     {results['ABC']['accidental']:>10.2f} Hz")
    print(f"  True coincidences:        {results['ABC']['true_coinc']:>10.2f} Hz")
    print(f"  Accidental fraction:      {results['ABC']['accidental_fraction']*100:>10.2f} %")
    print()

    # Interpretation
    print("Interpretation:")
    if results['AB']['accidental_fraction'] > 0.5:
        print("  ⚠️  WARNING: Accidentals dominate (>50% of measured coincidences)")
        print("      Consider: increasing detector spacing, improving time resolution,")
        print("      or verifying that sources are actually correlated.")
    elif results['AB']['accidental_fraction'] > 0.1:
        print("  ⚠️  CAUTION: Significant accidental contribution (>10%)")
        print("      Accidental correction is important for accurate results.")
    else:
        print("  ✓ Accidental fraction is small (<10%)")
        print("    Measured coincidences are primarily true coincidences.")
    print()

    if results['AB']['significance'] > 5:
        print(f"  ✓ True coincidences are highly significant ({results['AB']['significance']:.1f}σ)")
    elif results['AB']['significance'] > 3:
        print(f"  ✓ True coincidences are significant ({results['AB']['significance']:.1f}σ)")
    else:
        print(f"  ⚠️  Low statistical significance ({results['AB']['significance']:.1f}σ)")
        print("     Consider longer measurement time for better statistics.")
    print()


def plot_results(data, results):
    """Create visualization of coincidence analysis."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Time series of rates
    ax1 = axes[0, 0]
    samples = np.arange(len(data['rate_A']))
    ax1.plot(samples, data['rate_A'], 'o-', label='A singles', alpha=0.7)
    ax1.plot(samples, data['rate_B'], 's-', label='B singles', alpha=0.7)
    ax1.plot(samples, data['coinc_AB'], '^-', label='A-B coinc', alpha=0.7)
    ax1.set_xlabel('Sample Number')
    ax1.set_ylabel('Rate (Hz)')
    ax1.set_title('Count Rates Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Coincidence breakdown
    ax2 = axes[0, 1]
    categories = ['A-B', 'A-C', 'A-B-C']
    measured = [results['AB']['mean_coinc'],
                results['AC']['mean_coinc'],
                results['ABC']['mean_coinc']]
    accidental = [results['AB']['accidental'],
                  results['AC']['accidental'],
                  results['ABC']['accidental']]
    true = [results['AB']['true_coinc'],
            results['AC']['true_coinc'],
            results['ABC']['true_coinc']]

    x = np.arange(len(categories))
    width = 0.25

    ax2.bar(x - width, measured, width, label='Measured', alpha=0.8)
    ax2.bar(x, accidental, width, label='Accidental', alpha=0.8)
    ax2.bar(x + width, true, width, label='True', alpha=0.8)

    ax2.set_xlabel('Coincidence Type')
    ax2.set_ylabel('Rate (Hz)')
    ax2.set_title('Coincidence Rate Breakdown')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Distribution of A-B coincidences
    ax3 = axes[1, 0]
    ax3.hist(data['coinc_AB'], bins=15, alpha=0.7, edgecolor='black')
    ax3.axvline(results['AB']['mean_coinc'], color='red', linestyle='--',
                linewidth=2, label=f"Mean: {results['AB']['mean_coinc']:.2f} Hz")
    ax3.axvline(results['AB']['accidental'], color='orange', linestyle='--',
                linewidth=2, label=f"Accidental: {results['AB']['accidental']:.2f} Hz")
    ax3.set_xlabel('A-B Coincidence Rate (Hz)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Distribution of A-B Coincidence Rates')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Correlation plot (singles vs coincidences)
    ax4 = axes[1, 1]
    ax4.scatter(data['rate_A'] * data['rate_B'], data['coinc_AB'],
                alpha=0.6, s=50, edgecolors='black', linewidths=0.5)

    # Theoretical line for pure accidentals
    product_range = np.linspace(0, (data['rate_A'] * data['rate_B']).max(), 100)
    tau = 10e-9
    theoretical = 2 * tau * product_range

    ax4.plot(product_range, theoretical, 'r--', linewidth=2,
             label='Expected (accidentals only)')

    ax4.set_xlabel('R_A × R_B (Hz²)')
    ax4.set_ylabel('A-B Coincidence Rate (Hz)')
    ax4.set_title('Coincidences vs Product of Singles Rates')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('accidental_analysis.png', dpi=150)
    print("Plot saved as 'accidental_analysis.png'")
    plt.show()


def main():
    print("=" * 70)
    print("CD48 Accidental Coincidence Analysis")
    print("=" * 70)
    print()

    with CD48() as cd48:
        print(f"Connected to CD48 - Firmware: {cd48.get_version()}")
        print()

        # Configure channels
        print("Configuring channels...")
        cd48.set_channel(0, A=1, B=0, C=0, D=0)  # A singles
        cd48.set_channel(1, A=0, B=1, C=0, D=0)  # B singles
        cd48.set_channel(2, A=0, B=0, C=1, D=0)  # C singles
        cd48.set_channel(4, A=1, B=1, C=0, D=0)  # A-B coincidence
        cd48.set_channel(5, A=1, B=0, C=1, D=0)  # A-C coincidence
        cd48.set_channel(6, A=0, B=1, C=1, D=0)  # B-C coincidence
        cd48.set_channel(7, A=1, B=1, C=1, D=0)  # A-B-C triple

        cd48.set_trigger_level(0.5)
        cd48.set_impedance_50ohm()
        print()

        # Measurement parameters
        num_samples = 30  # Number of measurements
        interval = 2.0    # Integration time per measurement (seconds)

        print(f"Measurement parameters:")
        print(f"  Number of samples: {num_samples}")
        print(f"  Integration time: {interval}s per sample")
        print(f"  Total time: ~{num_samples * interval:.0f}s")
        print()

        # Measure data
        data = measure_rates(cd48, num_samples=num_samples, interval=interval)

        # Analyze
        print("Analyzing data...")
        tau = 10e-9  # 10 ns coincidence window
        results = analyze_coincidences(data, tau=tau)
        print()

        # Display results
        print_results(results)

        # Plot
        print("Generating plots...")
        plot_results(data, results)


if __name__ == "__main__":
    main()
