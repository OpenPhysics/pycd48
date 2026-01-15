"""
Device Information Example

Simple script to test connection and display device information.
"""

from pycd48 import CD48


def main():
    try:
        # Connect to CD48
        print("Attempting to connect to CD48...")
        with CD48() as cd48:
            print("Successfully connected!")
            print()

            # Get version
            version = cd48.get_version()
            print(f"Firmware Version: {version}")
            print()

            # Get current settings
            print("Current Device Settings:")
            print(cd48.get_settings(human_readable=True))
            print()

            # Display help
            print("Available Commands:")
            print(cd48.help())
            print()

            # Test LEDs
            print("Testing LEDs (will light up for 1 second)...")
            cd48.test_leds()
            print("LED test complete!")

    except ValueError as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure the CD48 is connected via USB")
        print("  2. Check that you have permissions to access the serial port")
        print("     On Linux, you may need to add your user to the 'dialout' group:")
        print("     sudo usermod -a -G dialout $USER")
        print("  3. Try specifying the port manually:")
        print("     CD48(port='/dev/ttyUSB0')  # Linux")
        print("     CD48(port='COM3')          # Windows")


if __name__ == "__main__":
    main()
