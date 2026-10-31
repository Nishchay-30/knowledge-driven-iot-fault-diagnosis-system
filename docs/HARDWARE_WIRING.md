# Hardware Wiring Guide & Electrical Safety Specifications

## 1. Schematic Overview

```
                      +-------------------+
                      | 12V 2A DC Supply  |
                      +---+-----------+---+
                          | +12V      | GND (Common Ground)
                          |           |
            +-------------+-----------+---------------------+
            |                         |                     |
            v +12V                    v GND                 |
     +--------------+          +--------------+             |
     | L298N Driver |          | ESP32 DevKit |             |
     |              |          |              |             |
     | ENA <--------+-- GPIO19 | 3V3 -------->| Power Rails |
     | IN1 <--------+-- GPIO25 | GND ---------+ (Shared GND)|
     | IN2 <--------+-- GPIO26 |              |             |
     | OUT1/OUT2    |          | GPIO21 (SDA)-+-> MPU6050   |
     +-------+------+          | GPIO22 (SCL)-+-> MPU6050   |
             |                 |              |             |
             v                 | GPIO4 (DQ) --+-> DS18B20   |
       [12V DC Motor]          |              |  (4.7k Pull)|
             |                 | GPIO36 (ADC)-+<- Voltage   |
             +-> [ACS712 5A] ->|              |   Divider   |
                   (VCC=5V)    | GPIO18 (IRQ)-+<- IR Sensor |
                               |              |             |
                               | GPIO2 (LED) -+-> Red LED   |
                               | GPIO15 (BUZZ)+-> Buzzer    |
                               +--------------+             |
                                      |                     |
                                      +---------------------+
```

---

## 2. Complete Pin Connection Matrix

| ESP32 Pin | Function | Sensor / Peripheral | Peripheral Pin | Notes & Conditioning |
|---|---|---|---|---|
| **3V3** | 3.3V Power Out | MPU6050, DS18B20 | VCC / VDD | Connect to 3.3V bus on breadboard. |
| **GND** | Ground Reference | All sensors, L298N, PS | GND | **Common Ground** shared across all supplies. |
| **GPIO 21** | I2C Data (SDA) | MPU6050 | SDA | Standard ESP32 hardware I2C data. |
| **GPIO 22** | I2C Clock (SCL) | MPU6050 | SCL | Standard ESP32 hardware I2C clock. |
| **GPIO 4** | 1-Wire Digital | DS18B20 | DQ (Data) | Requires **4.7kΩ pull-up resistor** to 3V3. |
| **GPIO 36** | Analog ADC1 CH0 | ACS712-05B | OUT (via divider) | **CRITICAL: Connect via 10k/20k voltage divider.** |
| **GPIO 18** | External Interrupt | Optical Slot Sensor | OUT / DO | Measures pulses from slotted encoder disc. |
| **GPIO 2** | Digital Output | Status Warning LED | Anode | Connect via 330Ω current-limiting resistor to GND. |
| **GPIO 15** | Digital Output | Piezo Buzzer | Base (2N2222) | Drive via NPN transistor to prevent over-current. |
| **GPIO 19** | PWM Output | L298N | ENA | PWM speed modulation (frequency 5 kHz, 8-bit). |
| **GPIO 25** | Digital Output | L298N | IN1 | Motor direction control terminal 1. |
| **GPIO 26** | Digital Output | L298N | IN2 | Motor direction control terminal 2. |

---

## 3. Detailed Circuit Conditioning Diagrams

### A. ACS712 Voltage Divider Circuit
ACS712 is powered by 5V and outputs $2.5\,\text{V} \pm 185\,\text{mV/A}$. At maximum current, output can reach $5\,\text{V}$.
```
ACS712 (OUT) ----[ 10 kΩ (R1) ]----+-----> ESP32 GPIO 36 (ADC1 CH0)
                                   |
                             [ 20 kΩ (R2) ]
                                   |
                                  GND

Division Ratio = 20k / (10k + 20k) = 0.6667
Max Voltage at GPIO 36 = 5.0V * 0.6667 = 3.33V (Safe for ESP32 ADC)
```

### B. DS18B20 1-Wire Temperature Pull-Up Circuit
```
     3.3V Rail
        |
      [ 4.7 kΩ ]
        |
DS18B20 (DQ) -----------------------------> ESP32 GPIO 4
```

### C. Buzzer Transistor Driver Circuit
```
ESP32 GPIO 15 ----[ 1 kΩ ]----> Base (2N2222 NPN)
                                Collector ----[ Piezo Buzzer ]----> 5V / 12V
                                Emitter --------------------------> GND
```

---

## 4. Pre-Power Electrical Checklist

- [ ] Verify common ground (`GND`) links the 12V supply, ESP32, L298N, and sensors.
- [ ] Measure resistance across voltage divider ($R_1 = 10\,\text{k}\Omega$, $R_2 = 20\,\text{k}\Omega$) before connecting to GPIO 36.
- [ ] Ensure 4.7kΩ pull-up resistor is installed on DS18B20 data line.
- [ ] Verify L298N onboard 5V regulator jumper is enabled if supplying logic from L298N.
- [ ] Confirm no stray DuPont wires short 12V rail to 3.3V logic pins.
