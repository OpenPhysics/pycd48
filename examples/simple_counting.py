"""
Simple Counting Example

This example demonstrates basic usage of the CD48 to count events
on different channels and measure coincidences.
"""

import time
from pycd48 import CD48


def main() -> None:
    # Connect to CD48
    # Auto-detects port, or specify: CD48(port='COM3') on Windows
    # or CD48(port='/dev/ttyUSB0') on Linux
    with CD48() as cd48:
        print("Connected to CD48")
        print(f"Firmware version: {cd48.get_version()}")
        print()

        # Configure counters
        print("Configuring counters...")
        cd48.set_channel(0, A=1, B=0, C=0, D=0)  # Counter 0: singles on A
        cd48.set_channel(1, A=0, B=1, C=0, D=0)  # Counter 1: singles on B
        cd48.set_channel(2, A=0, B=0, C=1, D=0)  # Counter 2: singles on C
        cd48.set_channel(3, A=0, B=0, C=0, D=1)  # Counter 3: singles on D
        cd48.set_channel(4, A=1, B=1, C=0, D=0)  # Counter 4: A-B coincidences
        cd48.set_channel(5, A=1, B=0, C=1, D=0)  # Counter 5: A-C coincidences
        cd48.set_channel(6, A=0, B=1, C=1, D=0)  # Counter 6: B-C coincidences
        cd48.set_channel(7, A=1, B=1, C=1, D=0)  # Counter 7: A-B-C triple coincidences

        # Set trigger level (e.g., 0.5V)
        print("Setting trigger level to 0.5V")
        cd48.set_trigger_level(0.5)

        # Set to 50 Ohm impedance
        print("Setting 50 Ohm impedance")
        cd48.set_impedance_50ohm()

        # Display current settings
        print("\nCurrent settings:")
        print(cd48.get_settings(human_readable=True))
        print()

        # Clear counters
        print("Clearing counters and starting measurement...")
        cd48.clear_counts()

        # Measurement duration
        duration = 10  # seconds
        print(f"Counting for {duration} seconds...")
        time.sleep(duration)

        # Read results
        data = cd48.get_counts(human_readable=False)
        counts = data["counts"]
        overflow = data["overflow"]

        # Display results
        print(f"\nResults after {duration} seconds:")
        print(f"  Channel A singles:     {counts[0]:8d} counts")
        print(f"  Channel B singles:     {counts[1]:8d} counts")
        print(f"  Channel C singles:     {counts[2]:8d} counts")
        print(f"  Channel D singles:     {counts[3]:8d} counts")
        print(f"  A-B coincidences:      {counts[4]:8d} counts")
        print(f"  A-C coincidences:      {counts[5]:8d} counts")
        print(f"  B-C coincidences:      {counts[6]:8d} counts")
        print(f"  A-B-C triple coinc.:   {counts[7]:8d} counts")

        if overflow:
            print(f"\n  WARNING: Counter overflow detected! (0x{overflow:02X})")

        # Calculate rates
        print(f"\nCount rates (counts per second):")
        print(f"  Channel A rate:        {counts[0]/duration:8.2f} Hz")
        print(f"  Channel B rate:        {counts[1]/duration:8.2f} Hz")
        print(f"  Channel C rate:        {counts[2]/duration:8.2f} Hz")
        print(f"  Channel D rate:        {counts[3]/duration:8.2f} Hz")
        print(f"  A-B coincidence rate:  {counts[4]/duration:8.2f} Hz")


if __name__ == "__main__":
    main()
