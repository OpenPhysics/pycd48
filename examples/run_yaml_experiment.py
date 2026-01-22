"""
Run Experiment from YAML Configuration

This example demonstrates how to run experiments using YAML configuration files.
This approach provides better reproducibility and easier collaboration compared
to hardcoding experiment parameters in Python scripts.

Usage:
    python run_yaml_experiment.py configs/simple_coincidence.yaml
    python run_yaml_experiment.py configs/cosmic_ray_telescope.yaml
    python run_yaml_experiment.py configs/voltage_sweep.yaml
"""

import argparse
import sys
from pathlib import Path

from pycd48 import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run CD48 experiment from YAML configuration file"
    )
    parser.add_argument("config", type=str, help="Path to YAML configuration file")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        import logging

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    config_path = Path(args.config)

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)

    print("=" * 70)
    print(f"Running experiment from: {config_path}")
    print("=" * 70)
    print()

    try:
        # Run the experiment
        result = run_experiment(config_path)

        # Display results
        print()
        print("=" * 70)
        print("EXPERIMENT COMPLETED")
        print("=" * 70)
        print()

        # Print experiment metadata
        metadata = result.get("metadata", {})
        print(f"Experiment type: {metadata.get('experiment_type', 'unknown')}")
        print()

        # Print key results based on experiment type
        data = result.get("data", {})
        exp_type = metadata.get("experiment_type", "")

        if exp_type == "rate":
            if "mean_rate" in data:
                print(
                    f"Mean count rate: {data['mean_rate']:.2f} ± {data.get('std_rate', 0):.2f} Hz"
                )
                print(f"Number of measurements: {data.get('repeats', 1)}")
            else:
                print(f"Count rate: {data.get('rate', 0):.2f} Hz")
                print(f"Total counts: {data.get('counts', 0)}")
                print(f"Duration: {data.get('duration', 0):.1f} s")

        elif exp_type == "coincidence":
            if "mean_true_coincidence_rate" in data:
                print(
                    f"Mean true coincidence rate: {data['mean_true_coincidence_rate']:.2f} "
                    f"± {data.get('std_true_coincidence_rate', 0):.2f} Hz"
                )
                print(f"Number of measurements: {data.get('repeats', 1)}")
            else:
                print(f"Singles A rate: {data.get('rate_a', 0):.2f} Hz")
                print(f"Singles B rate: {data.get('rate_b', 0):.2f} Hz")
                print(f"Coincidence rate: {data.get('coincidence_rate', 0):.2f} Hz")
                print(f"Accidental rate: {data.get('accidental_rate', 0):.4f} Hz")
                print(f"True coincidence rate: {data.get('true_coincidence_rate', 0):.2f} Hz")

        elif exp_type == "continuous":
            import numpy as np

            channels = data.get("channels", [])
            rates = data.get("rates", {})
            num_measurements = metadata.get("num_measurements", 0)

            print(f"Duration: {metadata.get('duration', 0):.1f} s")
            print(f"Number of measurements: {num_measurements}")
            print(f"Interval: {data.get('interval', 0):.1f} s")
            print()
            print("Channel statistics:")
            for ch in channels:
                if ch in rates:
                    ch_rates = rates[ch]
                    mean_rate = np.mean(ch_rates)
                    std_rate = np.std(ch_rates)
                    print(f"  Channel {ch}: {mean_rate:.2f} ± {std_rate:.2f} Hz")

        elif exp_type == "voltage_sweep":
            import numpy as np

            voltages = data.get("voltages", [])
            rates = data.get("rates", {})
            channels = data.get("channels", [])

            print(f"Voltage range: {min(voltages):.2f} - {max(voltages):.2f} V")
            print(f"Number of points: {len(voltages)}")
            print(f"Measurement time per point: {data.get('measurement_time', 0):.1f} s")
            print()

            # Find optimal voltage (maximum rate for first channel)
            if channels and channels[0] in rates:
                ch = channels[0]
                ch_rates = rates[ch]
                max_idx = np.argmax(ch_rates)
                print(
                    f"Optimal voltage (channel {ch}): {voltages[max_idx]:.2f} V "
                    f"(rate: {ch_rates[max_idx]:.2f} Hz)"
                )

        print()

        # Show output file locations
        config = result.get("config", {})
        output = config.get("output", {})
        if output:
            output_dir = output.get("directory", ".")
            exp_name = config.get("name", "experiment")
            import time

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            base_name = f"{exp_name}_{timestamp}"

            print("Output files:")
            if output.get("json"):
                print(f"  JSON: {output_dir}/{base_name}.json")
            if output.get("csv"):
                print(f"  CSV:  {output_dir}/{base_name}.csv")

    except Exception as e:
        print(f"Error running experiment: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
