# CD48 Web Interface

A browser-based interface for the CD48 Coincidence Counter using the Web Serial API.

## Requirements

- **Browser**: Chrome 89+ or Edge 89+ (Web Serial API support required)
- **CD48 Device**: Connected via USB

> **Note**: Firefox and Safari do not support the Web Serial API.

## Quick Start

### Option 1: Run Locally (Recommended)

The easiest way to run the web interface is using Python's built-in HTTP server:

```bash
cd web
python -m http.server 8000
```

Then open http://localhost:8000 in Chrome or Edge.

### Option 2: Using Node.js

```bash
cd web
npx serve .
```

### Option 3: Direct File Access

You can open `index.html` directly in Chrome/Edge, but some browsers restrict Web Serial API access for `file://` URLs. Using a local server is recommended.

## Usage

1. **Connect the CD48** to your computer via USB
2. **Open the web interface** in Chrome or Edge
3. **Click "Connect"** and select the CD48 from the port picker
4. **View counts** and adjust settings in real-time

### Features

- **Real-time count display** for all 8 channels
- **Auto-refresh mode** with rate calculation
- **Trigger level adjustment** (0-4.08V)
- **Impedance selection** (50Ω or High-Z)
- **DAC output control** (0-4.08V)
- **LED test** function
- **Activity log** for debugging

## JavaScript API

The `cd48.js` library provides a clean API for controlling the CD48:

```javascript
// Create instance and connect
const cd48 = new CD48();
await cd48.connect();

// Get firmware version
const version = await cd48.getVersion();
console.log('Firmware:', version);

// Read counts
const data = await cd48.getCounts();
console.log('Counts:', data.counts);
console.log('Overflow:', data.overflow);

// Set trigger level (0-4.08V)
await cd48.setTriggerLevel(0.5);

// Set impedance
await cd48.setImpedance50Ohm();
await cd48.setImpedanceHighZ();

// Measure rate on a channel
const result = await cd48.measureRate(0, 10);  // Channel 0, 10 seconds
console.log(`Rate: ${result.rate} Hz`);

// Measure coincidences with accidental correction
const coincidence = await cd48.measureCoincidenceRate({
    duration: 60,
    singlesAChannel: 0,
    singlesBChannel: 1,
    coincidenceChannel: 4
});
console.log(`True coincidence rate: ${coincidence.trueCoincidenceRate} Hz`);

// Disconnect
await cd48.disconnect();
```

### API Reference

#### Connection

- `CD48.isSupported()` - Check if Web Serial API is available
- `connect()` - Open connection (shows port picker)
- `disconnect()` - Close connection
- `isConnected()` - Check connection status

#### Counts

- `getCounts(humanReadable)` - Read counts from all channels
- `clearCounts()` - Clear all counters
- `getOverflow()` - Get and clear overflow status

#### Configuration

- `setChannel(channel, {A, B, C, D})` - Configure counter inputs
- `setTriggerLevel(voltage)` - Set trigger threshold (0-4.08V)
- `setImpedance50Ohm()` - Set 50Ω impedance
- `setImpedanceHighZ()` - Set high-Z impedance
- `setDacVoltage(voltage)` - Set DAC output (0-4.08V)
- `setRepeat(intervalMs)` - Set auto-report interval
- `toggleRepeat()` - Toggle auto-reporting

#### Device Info

- `getVersion()` - Get firmware version
- `getSettings(humanReadable)` - Get current settings
- `getHelp()` - Get built-in help text
- `testLeds()` - Test all LEDs

#### High-Level Measurements

- `measureRate(channel, duration)` - Measure count rate
- `measureCoincidenceRate(options)` - Measure coincidences with accidental correction

## Troubleshooting

### "Web Serial API not supported"

Use Chrome 89+ or Edge 89+. Firefox and Safari don't support Web Serial.

### "No CD48 device selected"

- Make sure the CD48 is connected via USB
- Check that no other application (PuTTY, Python, etc.) is using the port
- Try unplugging and reconnecting the device

### Port picker is empty

- The CD48 may not be recognized. Try clicking "Connect" anyway and check for any serial devices.
- On Linux, you may need to add your user to the `dialout` group.

### Connection works but no data

- Check that the correct baud rate is being used (115200)
- Try refreshing the page and reconnecting
- Check the Activity Log for error messages

## Security Notes

The Web Serial API requires:
- User gesture (click) to initiate connection
- Explicit port selection by the user
- HTTPS or localhost (not plain HTTP on remote servers)

This ensures the browser can't silently access serial devices without user consent.

## Browser Compatibility

| Browser | Support |
|---------|---------|
| Chrome 89+ | Full support |
| Edge 89+ | Full support |
| Opera 76+ | Full support |
| Firefox | Not supported |
| Safari | Not supported |

## Files

- `index.html` - Main web interface
- `cd48.js` - JavaScript library for CD48 communication
- `README.md` - This documentation
