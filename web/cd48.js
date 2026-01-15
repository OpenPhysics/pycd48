/**
 * CD48 Coincidence Counter - Web Serial API Interface
 *
 * A JavaScript library for controlling the Red Dog Physics CD48
 * Coincidence Counter via the Web Serial API.
 *
 * Requires Chrome 89+ or Edge 89+
 *
 * @example
 * const cd48 = new CD48();
 * await cd48.connect();
 * const version = await cd48.getVersion();
 * console.log('Firmware:', version);
 * const counts = await cd48.getCounts();
 * console.log('Counts:', counts);
 * await cd48.disconnect();
 */

class CD48 {
    /**
     * Create a CD48 interface instance.
     * @param {Object} options - Configuration options
     * @param {number} options.baudRate - Baud rate (default: 115200)
     * @param {number} options.commandDelay - Delay after commands in ms (default: 50)
     */
    constructor(options = {}) {
        this.baudRate = options.baudRate || 115200;
        this.commandDelay = options.commandDelay || 50;
        this.port = null;
        this.reader = null;
        this.writer = null;
        this.readableStreamClosed = null;
        this.writableStreamClosed = null;
    }

    /**
     * Check if Web Serial API is supported.
     * @returns {boolean}
     */
    static isSupported() {
        return 'serial' in navigator;
    }

    /**
     * Connect to the CD48 device.
     * Opens a serial port picker dialog for the user.
     * @returns {Promise<boolean>} True if connected successfully
     */
    async connect() {
        if (!CD48.isSupported()) {
            throw new Error('Web Serial API not supported. Use Chrome or Edge.');
        }

        try {
            // Request port with Cypress VID filter
            this.port = await navigator.serial.requestPort({
                filters: [{ usbVendorId: 0x04B4 }]  // Cypress Semiconductor
            });

            await this.port.open({ baudRate: this.baudRate });

            // Set up reader and writer
            const textDecoder = new TextDecoderStream();
            this.readableStreamClosed = this.port.readable.pipeTo(textDecoder.writable);
            this.reader = textDecoder.readable.getReader();

            const textEncoder = new TextEncoderStream();
            this.writableStreamClosed = textEncoder.readable.pipeTo(this.port.writable);
            this.writer = textEncoder.writable.getWriter();

            // Wait for device to initialize
            await this.sleep(500);

            return true;
        } catch (error) {
            if (error.name === 'NotFoundError') {
                throw new Error('No CD48 device selected.');
            }
            throw error;
        }
    }

    /**
     * Disconnect from the CD48 device.
     */
    async disconnect() {
        if (this.reader) {
            await this.reader.cancel();
            await this.readableStreamClosed.catch(() => {});
            this.reader = null;
        }
        if (this.writer) {
            await this.writer.close();
            await this.writableStreamClosed;
            this.writer = null;
        }
        if (this.port) {
            await this.port.close();
            this.port = null;
        }
    }

    /**
     * Check if connected to device.
     * @returns {boolean}
     */
    isConnected() {
        return this.port !== null && this.reader !== null;
    }

    /**
     * Sleep for specified milliseconds.
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Send a command and read the response.
     * @param {string} command - Command to send
     * @returns {Promise<string>} Response from device
     */
    async sendCommand(command) {
        if (!this.isConnected()) {
            throw new Error('Not connected to CD48');
        }

        // Clear any pending data
        await this.writer.write(command + '\r');
        await this.sleep(this.commandDelay);

        // Read response with timeout
        let response = '';
        const startTime = Date.now();
        const timeout = 1000;

        while (Date.now() - startTime < timeout) {
            const { value, done } = await Promise.race([
                this.reader.read(),
                this.sleep(100).then(() => ({ value: '', done: false, timeout: true }))
            ]);

            if (done) break;
            if (value) response += value;

            // Check if we have a complete response
            if (response.includes('\r') || response.includes('\n')) {
                break;
            }
        }

        return response.trim();
    }

    /**
     * Get firmware version.
     * @returns {Promise<string>}
     */
    async getVersion() {
        return await this.sendCommand('v');
    }

    /**
     * Get help text from device.
     * @returns {Promise<string>}
     */
    async getHelp() {
        return await this.sendCommand('H');
    }

    /**
     * Get current counts from all channels.
     * @param {boolean} humanReadable - If true, returns formatted string
     * @returns {Promise<Object|string>} Counts data or formatted string
     */
    async getCounts(humanReadable = false) {
        if (humanReadable) {
            return await this.sendCommand('C');
        }

        const response = await this.sendCommand('c');
        const parts = response.split(/\s+/).filter(p => p.length > 0);

        if (parts.length >= 9) {
            return {
                counts: parts.slice(0, 8).map(Number),
                overflow: parseInt(parts[8])
            };
        }

        throw new Error(`Unexpected response format: ${response}`);
    }

    /**
     * Clear all counters by reading them.
     */
    async clearCounts() {
        await this.getCounts(false);
    }

    /**
     * Get current settings.
     * @param {boolean} humanReadable - If true, returns formatted string
     * @returns {Promise<string>}
     */
    async getSettings(humanReadable = true) {
        return await this.sendCommand(humanReadable ? 'P' : 'p');
    }

    /**
     * Configure a counter channel.
     * @param {number} channel - Channel number (0-7)
     * @param {Object} inputs - Input configuration
     * @param {number} inputs.A - Enable input A (0 or 1)
     * @param {number} inputs.B - Enable input B (0 or 1)
     * @param {number} inputs.C - Enable input C (0 or 1)
     * @param {number} inputs.D - Enable input D (0 or 1)
     * @returns {Promise<string>}
     */
    async setChannel(channel, { A = 0, B = 0, C = 0, D = 0 } = {}) {
        if (channel < 0 || channel > 7) {
            throw new Error(`Channel must be 0-7, got ${channel}`);
        }
        return await this.sendCommand(`S${channel}${A}${B}${C}${D}`);
    }

    /**
     * Set trigger level voltage.
     * @param {number} voltage - Voltage threshold (0.0 to 4.08V)
     * @returns {Promise<string>}
     */
    async setTriggerLevel(voltage) {
        const byteVal = Math.max(0, Math.min(255, Math.round((voltage / 4.08) * 255)));
        return await this.sendCommand(`L${byteVal}`);
    }

    /**
     * Get trigger level as voltage.
     * @param {number} byteValue - Raw byte value (0-255)
     * @returns {number} Voltage (0.0 to 4.08V)
     */
    static byteToVoltage(byteValue) {
        return (byteValue / 255) * 4.08;
    }

    /**
     * Set input impedance to 50 Ohms.
     * @returns {Promise<string>}
     */
    async setImpedance50Ohm() {
        return await this.sendCommand('z');
    }

    /**
     * Set input impedance to High-Z.
     * @returns {Promise<string>}
     */
    async setImpedanceHighZ() {
        return await this.sendCommand('Z');
    }

    /**
     * Set automatic repeat interval.
     * @param {number} intervalMs - Interval in milliseconds (100-65535)
     * @returns {Promise<string>}
     */
    async setRepeat(intervalMs) {
        const clamped = Math.max(100, Math.min(65535, intervalMs));
        return await this.sendCommand(`r${clamped}`);
    }

    /**
     * Toggle automatic repeat mode.
     * @returns {Promise<string>}
     */
    async toggleRepeat() {
        return await this.sendCommand('R');
    }

    /**
     * Set DAC output voltage.
     * @param {number} voltage - Output voltage (0.0 to 4.08V)
     * @returns {Promise<string>}
     */
    async setDacVoltage(voltage) {
        const byteVal = Math.max(0, Math.min(255, Math.round((voltage / 4.08) * 255)));
        return await this.sendCommand(`V${byteVal}`);
    }

    /**
     * Get and clear overflow status.
     * @returns {Promise<number>} 8-bit overflow flag
     */
    async getOverflow() {
        const response = await this.sendCommand('E');
        return parseInt(response);
    }

    /**
     * Test all LEDs (lights for 1 second).
     * @returns {Promise<string>}
     */
    async testLeds() {
        return await this.sendCommand('T');
    }

    /**
     * Measure count rate on a channel.
     * @param {number} channel - Channel number (0-7)
     * @param {number} duration - Measurement duration in seconds
     * @returns {Promise<Object>} Rate measurement result
     */
    async measureRate(channel = 0, duration = 1.0) {
        if (channel < 0 || channel > 7) {
            throw new Error(`Channel must be 0-7, got ${channel}`);
        }

        await this.clearCounts();
        await this.sleep(duration * 1000);
        const data = await this.getCounts(false);
        const counts = data.counts[channel];

        return {
            counts: counts,
            duration: duration,
            rate: counts / duration,
            channel: channel
        };
    }

    /**
     * Measure coincidence rate with accidental correction.
     * @param {Object} options - Measurement options
     * @param {number} options.duration - Measurement duration in seconds
     * @param {number} options.singlesAChannel - Channel for singles A (default: 0)
     * @param {number} options.singlesBChannel - Channel for singles B (default: 1)
     * @param {number} options.coincidenceChannel - Channel for coincidences (default: 4)
     * @param {number} options.coincidenceWindow - Window in seconds (default: 25e-9)
     * @returns {Promise<Object>} Coincidence measurement result
     */
    async measureCoincidenceRate({
        duration = 1.0,
        singlesAChannel = 0,
        singlesBChannel = 1,
        coincidenceChannel = 4,
        coincidenceWindow = 25e-9
    } = {}) {
        await this.clearCounts();
        await this.sleep(duration * 1000);
        const data = await this.getCounts(false);

        const singlesA = data.counts[singlesAChannel];
        const singlesB = data.counts[singlesBChannel];
        const coincidences = data.counts[coincidenceChannel];

        const rateA = singlesA / duration;
        const rateB = singlesB / duration;
        const coincidenceRate = coincidences / duration;
        const accidentalRate = 2 * coincidenceWindow * rateA * rateB;
        const trueCoincidenceRate = Math.max(0, coincidenceRate - accidentalRate);

        return {
            singlesA,
            singlesB,
            coincidences,
            duration,
            rateA,
            rateB,
            coincidenceRate,
            accidentalRate,
            trueCoincidenceRate
        };
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CD48;
}
