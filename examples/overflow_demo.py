"""
Counter Overflow Detection and Handling

This example demonstrates how to detect and handle counter overflows,
which occur when count rates are very high or measurement intervals
are too long.

Counter limits:
- Counters 0-6: 24-bit (max 16,777,215)
- Counter 7:    16-bit (max 65,535)

This example shows:
- How to detect overflow conditions
- Which counters overflowed
- Strategies for avoiding overflow
- Automatic interval adjustment
"""

from typing import Tuple, List, Dict, Any
import time
from pycd48 import CD48


def check_overflow(cd48: CD48) -> Tuple[int, List[int]]:
    """
    Check overflow status and decode which counters overflowed.

    Returns:
    --------
    overflow_flag : int
        8-bit flag (bit n = counter n overflowed)
    overflowed_counters : list
        List of counter numbers that overflowed
    """
    overflow_flag = cd48.get_overflow()

    # Decode which counters overflowed
    overflowed_counters = []
    for i in range(8):
        if overflow_flag & (1 << i):
            overflowed_counters.append(i)

    return overflow_flag, overflowed_counters


def adaptive_measurement(cd48: CD48, target_duration: float = 60, max_count: int = 1000000) -> Dict[str, Any]:
    """
    Perform measurement with automatic interval adjustment to prevent overflow.

    Parameters:
    -----------
    cd48 : CD48
        Connected CD48 device
    target_duration : float
        Total measurement duration (seconds)
    max_count : int
        Maximum counts before adjusting interval (safety margin)

    Returns:
    --------
    data : dict
        Collected data
    """
    print(f"Starting adaptive measurement ({target_duration}s total)")
    print(f"Safety limit: {max_count:,} counts")
    print()

    interval = 5.0  # Start with 5 second intervals
    start_time = time.time()

    all_data = {
        'times': [],
        'intervals': [],
        'counts': [[] for _ in range(8)],
        'overflows': []
    }

    print(f"{'Time(s)':<8} {'Interval(s)':<12} {'Ch0':<10} {'Ch1':<10} {'Overflow':<10}")
    print("-" * 60)

    while time.time() - start_time < target_duration:
        # Clear and measure
        cd48.clear_counts()
        time.sleep(interval)

        # Get data
        data = cd48.get_counts(human_readable=False)
        elapsed = time.time() - start_time

        # Check for overflow
        overflow_flag, overflowed = check_overflow(cd48)

        # Store data
        all_data['times'].append(elapsed)
        all_data['intervals'].append(interval)
        for i in range(8):
            all_data['counts'][i].append(data['counts'][i])
        all_data['overflows'].append(overflow_flag)

        # Display
        overflow_str = f"0x{overflow_flag:02X}" if overflow_flag else "OK"
        print(f"{elapsed:<8.1f} {interval:<12.1f} {data['counts'][0]:<10} "
              f"{data['counts'][1]:<10} {overflow_str:<10}")

        if overflowed:
            print(f"  ⚠️  Overflow detected on counters: {overflowed}")
            # Reduce interval to prevent future overflow
            interval = max(1.0, interval * 0.5)
            print(f"  → Reducing interval to {interval}s")
        else:
            # Check if counts are getting too high
            max_count_this_interval = max(data['counts'][:-1])  # Exclude ch7 (16-bit)

            # If we're approaching the limit, reduce interval
            if max_count_this_interval > max_count:
                old_interval = interval
                interval = max(1.0, interval * 0.7)
                print(f"  ! High count rate detected ({max_count_this_interval:,})")
                print(f"  → Reducing interval from {old_interval}s to {interval}s")

            # If counts are very low, we can increase interval for better statistics
            elif max_count_this_interval < max_count * 0.1 and interval < 10.0:
                interval = min(10.0, interval * 1.5)

    print()
    return all_data


def main() -> None:
    print("=" * 70)
    print("CD48 Counter Overflow Detection and Handling")
    print("=" * 70)
    print()

    print("Counter Limits:")
    print("  Counters 0-6: 24-bit (max 16,777,215 counts)")
    print("  Counter 7:    16-bit (max 65,535 counts)")
    print()
    print("This example demonstrates overflow detection and adaptive")
    print("interval adjustment to prevent data loss.")
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
        cd48.set_channel(4, A=1, B=1, C=0, D=0)  # A-B
        cd48.set_channel(5, A=1, B=0, C=1, D=0)  # A-C
        cd48.set_channel(6, A=0, B=1, C=1, D=0)  # B-C
        cd48.set_channel(7, A=1, B=1, C=1, D=0)  # A-B-C (16-bit!)

        cd48.set_trigger_level(0.5)
        cd48.set_impedance_50ohm()
        print()

        # First, demonstrate overflow detection
        print("=" * 70)
        print("TEST 1: Manual Overflow Check")
        print("=" * 70)
        print()

        # Get initial overflow status
        initial_overflow, initial_overflowed = check_overflow(cd48)

        if initial_overflow:
            print(f"Overflow flag: 0x{initial_overflow:02X}")
            print(f"Overflowed counters: {initial_overflowed}")
            print("(Overflow flag cleared)")
        else:
            print("No overflow detected")
        print()

        # Run adaptive measurement
        print("=" * 70)
        print("TEST 2: Adaptive Interval Measurement")
        print("=" * 70)
        print()

        data = adaptive_measurement(cd48, target_duration=30, max_count=1000000)

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print()

        total_overflows = sum(1 for x in data['overflows'] if x > 0)
        print(f"Total measurements: {len(data['times'])}")
        print(f"Overflow events: {total_overflows}")
        print(f"Interval range: {min(data['intervals']):.1f}s - {max(data['intervals']):.1f}s")
        print()

        # Calculate total counts
        print("Total Counts Collected:")
        for i in range(8):
            total = sum(data['counts'][i])
            counter_type = "24-bit" if i < 7 else "16-bit"
            max_val = 16777215 if i < 7 else 65535
            utilization = (total / max_val) * 100 if total > 0 else 0
            print(f"  Counter {i} ({counter_type}): {total:>12,} "
                  f"(max utilization: {utilization:.1f}%)")
        print()

        print("=" * 70)
        print("BEST PRACTICES")
        print("=" * 70)
        print()
        print("To avoid overflow:")
        print("  1. Monitor count rates and adjust measurement intervals")
        print("  2. Use shorter intervals for high count rates (>100 kHz)")
        print("  3. Reserve counter 7 for rare events (16-bit limit)")
        print("  4. Check overflow flag regularly with get_overflow()")
        print("  5. Consider using repeat mode for automatic data collection")
        print()
        print("Maximum safe interval examples (approximate):")
        print("  - At 1 kHz:     ~4.5 hours (24-bit) / 65 seconds (16-bit)")
        print("  - At 10 kHz:    ~28 minutes (24-bit) / 6.5 seconds (16-bit)")
        print("  - At 100 kHz:   ~2.8 minutes (24-bit) / 0.65 seconds (16-bit)")
        print("  - At 1 MHz:     ~16 seconds (24-bit) / 0.065 seconds (16-bit)")


if __name__ == "__main__":
    main()
