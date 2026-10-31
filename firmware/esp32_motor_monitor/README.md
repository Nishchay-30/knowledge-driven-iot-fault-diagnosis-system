# ESP32 Motor Telemetry & Fault Indication Firmware

This directory contains the production-grade Arduino C++ firmware for the **Knowledge-Driven IoT-Based Fault Diagnosis System**. It runs on an ESP32 DevKit to monitor a physical 12V DC motor, sample vibration RMS, temperature, current, and optical speed, publish telemetry to MQTT, and actuate physical alarms upon receiving diagnostic alert commands.

---

## 1. Hardware Pin Connections

| Sensor / Actuator | ESP32 GPIO | Electrical Connection & Safe Signal Conditioning |
|---|---|---|
| **MPU6050 Accelerometer** | **GPIO 21 (SDA)**<br>**GPIO 22 (SCL)** | Powered from **3.3V**. I2C bus utilizes internal/module 4.7kΩ pull-ups to 3.3V. |
| **DS18B20 Temp Probe** | **GPIO 4 (DQ)** | Powered from **3.3V**. Requires external **4.7kΩ pull-up resistor** between DQ and 3.3V. |
| **ACS712 Current Sensor** | **GPIO 36 (SENSOR_VP)** | Powered from 5V. **MUST use a voltage divider** (10kΩ series, 20kΩ to GND) to scale 0–5V output to safe 0–3.3V ADC range. |
| **IR Optical Slot Sensor** | **GPIO 18** | Open-collector / digital output with internal `INPUT_PULLUP`. Attached to falling-edge hardware interrupt. |
| **Warning LED** | **GPIO 2** | In series with a 220Ω / 330Ω current-limiting resistor to GND. |
| **Piezo Buzzer** | **GPIO 15** | Driven via 2N2222 NPN transistor or logic-level MOSFET with flyback diode. |
| **L298N Motor Driver** | **GPIO 19 (ENA)**<br>**GPIO 25 (IN1)**<br>**GPIO 26 (IN2)** | Logic signals driven from ESP32. 12V motor power rail kept isolated from ESP32 3.3V rail with common ground. |

> [!CAUTION]
> **Electrical Safety Warning:**
> 1. ESP32 GPIO pins are **NOT 5V tolerant**. Exposing GPIO 36 to direct 5V ACS712 output without a voltage divider can permanently destroy the ESP32 ADC.
> 2. Never power the 12V DC motor directly from the ESP32 5V or 3.3V pins. Always use a dedicated 12V 2A+ regulated DC power supply with a shared common ground (`GND`).

---

## 2. Sensor Signal Processing & Calibration

### A. Dynamic Vibration RMS (MPU6050)
- Takes a 64-sample window at 500 Hz ($2000\,\mu\text{s}$ interval).
- Computes mean static Z-acceleration (gravitational DC offset $\bar{a}$).
- Calculates dynamic AC deviation:
  $$\text{RMS}_g = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (a_i - \bar{a})^2}$$
- Converts $16384\,\text{LSB}/g$ to calibrated acceleration in $g$.

### B. Current Measurement (ACS712)
- Zero-current reference $V_{\text{zero}}$ is dynamically auto-calibrated during the first 256 samples on startup while the motor is stationary.
- Real-time current is calculated as:
  $$I\,(\text{Amperes}) = \frac{|V_{\text{pin}} / R_{\text{divider}} - V_{\text{zero\_terminal}}|}{\text{Sensitivity}\,(0.185\,\text{V/A})}$$
- Applies a 30 mA software deadband filter to eliminate idle noise.

### C. Optical Tachometer Speed (RPM)
- Measures optical slot interruptions using an ISR.
- Speed is calculated over a 500 ms window:
  $$\text{RPM} = \left(\frac{\text{Pulses}}{\text{Slots per Rev}}\right) \times \left(\frac{60000\,\text{ms}}{\Delta t_{\text{ms}}}\right)$$
- If no pulse arrives within 1500 ms, RPM resets cleanly to 0.0.

---

## 3. Build & Upload Instructions

### Using PlatformIO (Recommended)
1. Install PlatformIO Core (`pio`) or the VS Code PlatformIO extension.
2. Edit `include/config.h` to supply your WiFi SSID, WiFi password, and MQTT broker host IP.
3. Connect your ESP32 to your Mac via USB.
4. Run the build and upload command:
   ```bash
   pio run --target upload
   ```
5. Open the serial monitor at 115200 baud:
   ```bash
   pio device monitor -b 115200
   ```

### Using Arduino IDE
1. Install the ESP32 Board package via Boards Manager (`esp32` by Espressif).
2. Install required libraries from Library Manager:
   - `ArduinoJson` (v6.x)
   - `PubSubClient`
   - `OneWire`
   - `DallasTemperature`
   - `MPU6050` by Electronic Cats
3. Open `src/main.cpp` and copy `include/config.h` into the sketch folder.
4. Select board **ESP32 Dev Module** and port `/dev/cu.usbserial-*` or `/dev/cu.wchusbserial*`.
5. Click **Upload**.
