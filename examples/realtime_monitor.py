"""
Real-time Monitoring Example using Repeat Mode

This example demonstrates the CD48's automatic repeat mode, which
automatically reports counts at set intervals without needing to
poll the device repeatedly.

This is useful for:
- Real-time monitoring dashboards
- Reducing USB communication overhead
- Synchronizing data acquisition with external triggers
"""

import time
import sys
from pycd48 import CD48


def main() -> None:
    print("=" * 60)
    print("CD48 Real-time Monitor using Repeat Mode")
    print("=" * 60)
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

        # Set up repeat mode
        interval_ms = 1000  # Report every 1 second
        print(f"Setting up automatic reporting every {interval_ms}ms")
        cd48.set_repeat(interval_ms)

        # Enable repeat mode
        print("Enabling repeat mode...")
        cd48.toggle_repeat()  # Turn on
        print()

        print("Real-time monitoring started (Ctrl+C to stop)")
        print()
        print(f"{'Time':<12} {'Ch A':<10} {'Ch B':<10} {'A-B':<10} {'Rate A (Hz)':<12} {'Rate B (Hz)':<12}")
        print("-" * 80)

        try:
            count = 0
            start_time = time.time()

            while True:
                # In repeat mode, the device automatically sends data
                # We just need to read it from the serial buffer
                line = cd48.ser.readline().decode().strip()

                if line and not line.startswith('Repeat'):
                    # Parse the automatic output
                    # The device sends count data automatically
                    try:
                        # Try to get counts using our normal method
                        # (which will read the automatically sent data)
                        data = cd48.get_counts(human_readable=False)

                        elapsed = time.time() - start_time

                        # Calculate rates
                        rate_A = data['counts'][0] / (interval_ms / 1000)
                        rate_B = data['counts'][1] / (interval_ms / 1000)

                        # Display with timestamp
                        time_str = f"{elapsed:>8.1f}s"
                        print(f"{time_str:<12} {data['counts'][0]:<10} {data['counts'][1]:<10} "
                              f"{data['counts'][4]:<10} {rate_A:<12.1f} {rate_B:<12.1f}")

                        count += 1

                        # Show overflow warning if needed
                        if data['overflow']:
                            print(f"  ⚠️  WARNING: Counter overflow detected! (0x{data['overflow']:02X})")

                    except Exception as e:
                        # Just skip malformed lines
                        pass

                # Small sleep to prevent CPU spinning
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\nStopping monitor...")

        finally:
            # Disable repeat mode
            print("Disabling repeat mode...")
            cd48.toggle_repeat()  # Turn off

            print(f"\nMonitoring complete. Collected {count} data points.")
            print()
            print("Repeat mode advantages:")
            print("  - Automatic data delivery from device")
            print("  - Reduced USB polling overhead")
            print("  - More consistent timing intervals")
            print("  - Frees CPU for other tasks")


if __name__ == "__main__":
    main()
