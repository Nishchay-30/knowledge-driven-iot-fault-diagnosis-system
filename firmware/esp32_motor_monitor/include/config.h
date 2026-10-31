/**
 * @file config.h
 * @brief Configuration constants, pin mappings, and calibration parameters for ESP32 firmware.
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ==============================================================================
// 1. NETWORK & MQTT BROKER CONFIGURATION
// ==============================================================================
// Set your local 2.4 GHz WiFi credentials
#include "local_secrets.h"

// MQTT Broker Configuration
// For local testing on Mac: set to Mac's local LAN IP (e.g. 192.168.1.50) and port 1883
// For HiveMQ Cloud: set host to your instance (e.g. "xxxxxx.s1.eu.hivemq.cloud"), port 8883 (requires WiFiClientSecure)
#define MQTT_BROKER_HOST    "192.168.1.100"
#define MQTT_BROKER_PORT    1883
#define MQTT_CLIENT_ID      "esp32_motor01_hw"

// Device Identity & MQTT Topic Structure
#define DEVICE_ID           "motor01"
#define TOPIC_SENSORS       "iot/factory/motor01/sensors"
#define TOPIC_STATUS        "iot/factory/motor01/status"
#define TOPIC_ALERTS        "iot/factory/motor01/alerts"
#define TOPIC_COMMANDS      "iot/factory/motor01/commands"
#define TOPIC_COMMAND_ACK   "iot/factory/motor01/command_ack"

// Telemetry Publication Interval (milliseconds)
#define TELEMETRY_INTERVAL_MS 1000

// ==============================================================================
// 2. HARDWARE GPIO PIN MAPPINGS
// ==============================================================================
// DS18B20 1-Wire Digital Temperature Sensor (Requires external 4.7kΩ pull-up to 3.3V)
#define PIN_DS18B20         4

// MPU6050 6-Axis I2C Accelerometer / Gyroscope
#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

// ACS712-05B Hall-Effect Current Sensor (ADC1 CH0)
// ATTENTION: ACS712 outputs 0-5V. Use 10kΩ / 20kΩ voltage divider to scale to safe 0-3.3V ESP32 ADC range!
#define PIN_ACS712_ADC      36

// IR Optical Slot Sensor / Tachometer (External Interrupt)
#define PIN_IR_RPM          18

// Physical Alert Actuators
#define PIN_LED_ALERT       2    // Onboard blue LED or external red warning LED
#define PIN_BUZZER          15   // Piezo buzzer driver pin (active HIGH via NPN transistor)

// L298N Motor Driver Control Pins (Direction and PWM Speed)
#define PIN_L298N_ENA       19   // PWM Speed control pin
#define PIN_L298N_IN1       25   // Direction 1
#define PIN_L298N_IN2       26   // Direction 2

// ==============================================================================
// 3. SENSOR CALIBRATION & MEASUREMENT CONSTANTS
// ==============================================================================
// ACS712-05B Parameters:
// Sensitivity: 185 mV/A = 0.185 V/A
// Voltage Divider Ratio: R2 / (R1 + R2) -> 20k / (10k + 20k) = 0.6667
#define ACS712_SENSITIVITY_V_PER_A  0.185f
#define VOLTAGE_DIVIDER_RATIO       0.6667f
#define ESP32_ADC_VREF              3.30f
#define ESP32_ADC_RESOLUTION        4095.0f
#define ACS712_SAMPLES_COUNT        64

// Optical RPM Measurement Parameters:
// Number of slots/pulses per shaft revolution on the optical encoder disc
#define RPM_PULSES_PER_REV          20
#define RPM_CALC_INTERVAL_MS        500
#define RPM_TIMEOUT_MS              1500

// Vibration (MPU6050) RMS Window Parameters:
#define VIBE_SAMPLE_COUNT           64
#define VIBE_SAMPLE_DELAY_US        2000 // 500 Hz sampling rate

#endif // CONFIG_H
