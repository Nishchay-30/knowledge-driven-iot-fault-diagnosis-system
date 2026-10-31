# Layer 6 — Complete Real ESP32 Hardware Integration & Alerts

## 1. Objective
Extend the software architecture to physical microcontroller hardware. The complete cyber-physical loop operates as:
$$\text{Real Sensors} \to \text{ESP32} \to \text{MQTT Broker} \to \text{Node-RED / Python Ingestion} \to \text{Hybrid AI Engine} \to \text{Dashboard} \to \text{Physical Alert (LED/Buzzer)}$$

---

## 2. Hardware Bill of Materials (BOM)

| Component | Function | Operating Voltage | Interface to ESP32 |
|---|---|---|---|
| **ESP32 DevKit V1** | Edge Controller & MQTT Client | 5V (USB) / 3.3V Logic | Master Microcontroller |
| **12V DC Motor** | Monitored Rotary Machine | 12V Regulated DC | Driven via L298N H-Bridge |
| **MPU6050** | 6-Axis Accelerometer (Vibration) | 3.3V | I2C (SDA 21, SCL 22) |
| **DS18B20** | Digital Temperature Probe | 3.3V | 1-Wire (GPIO 4 with 4.7kΩ pullup) |
| **ACS712-05B** | Hall-Effect Current Sensor | 5V | ADC1 CH0 (GPIO 36 via 2:3 divider) |
| **Optical Slot Sensor** | Optical Tachometer (RPM) | 3.3V / 5V | Interrupt GPIO 18 (Active FALLING) |
| **L298N Driver** | Dual H-Bridge Motor Driver | 12V Motor / 5V Logic | GPIO 19 (PWM), GPIO 25, 26 (Dir) |
| **Warning LED** | Visual Alarm Indicator | 3.3V | GPIO 2 (with 330Ω resistor) |
| **Piezo Buzzer** | Acoustic Alarm Indicator | 5V / 12V | GPIO 15 (transistor driven) |
| **Power Supply** | 12V 2A Regulated DC Supply | 12V | Dedicated Motor Supply Rail |

---

## 3. Signal Conditioning & Electrical Precautions

> [!CAUTION]
> **Essential Safety Engineering Rules:**
> 1. **ADC Input Voltage Protection**: The ESP32 ADC pin cannot tolerate voltages above $3.3\,\text{V}$. The ACS712 outputs $0 - 5\,\text{V}$ ($2.5\,\text{V}$ nominal midpoint). A voltage divider ($R_1 = 10\,\text{k}\Omega$, $R_2 = 20\,\text{k}\Omega$) scales the maximum output from $5.0\,\text{V}$ down to $3.33\,\text{V}$.
> 2. **Power Isolation & Grounding**: The 12V motor power supply must be electrically isolated from the ESP32 logic power rail, with a single common ground connection (`GND`) to ensure an identical reference potential without ground loops.
> 3. **Inductive Flyback**: The L298N module includes internal flywheel clamping diodes to absorb inductive back-EMF spikes when motor coils de-energize.

---

## 4. Physical Alert Actuation Workflow

When the hybrid diagnostic engine classifies a critical fault:
1. Ingestion publishes an actionable alert payload to `iot/factory/motor01/alerts` with `actuate_hardware: true`.
2. The ESP32 callback parses the payload.
3. If `severity == "CRITICAL"`, the ESP32 energizes GPIO 2 (Warning LED) and sounds the Piezo buzzer on GPIO 15 for 2.5 seconds.
4. If an operator triggers an emergency stop command from the dashboard, the ESP32 pulls ENA LOW (GPIO 19), de-energizes the motor driver, and publishes `iot/factory/motor01/command_ack`.
5. Upon telemetry returning to nominal ranges, a recovery message clears the warning indicators.

---

## 5. Verification & Execution
To check connected serial ports and start the hardware monitoring ingestion:
```bash
./scripts/run_layer6.sh
```
To build and upload firmware to the ESP32:
```bash
cd firmware/esp32_motor_monitor
pio run --target upload
pio device monitor -b 115200
```
