/**
 * @file main.cpp
 * @brief ESP32 Motor Telemetry, MPU6050 RMS Vibration, DS18B20, ACS712 Current,
 *        Optical Tachometer RPM, and MQTT Physical Alert Actuation.
 *
 * System Architecture:
 * Real Sensors -> ESP32 -> MQTT Broker (Local / HiveMQ Cloud) -> Ingestion Pipeline -> Dashboard
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <MPU6050.h>

#include "config.h"

// -----------------------------------------------------------------------------
// Global Sensor Objects & State
// -----------------------------------------------------------------------------
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// DS18B20 Setup
OneWire oneWire(PIN_DS18B20);
DallasTemperature tempSensor(&oneWire);

// MPU6050 Accelerometer
MPU6050 mpu;
bool mpuInitialized = false;

// Optical Tachometer State
volatile unsigned long pulseCount = 0;
volatile unsigned long lastPulseTime = 0;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

// Timing Trackers
unsigned long lastTelemetryPublish = 0;
unsigned long lastRpmCalculation = 0;
unsigned long lastAlertBuzzTime = 0;

// Current Sensor Zero Calibration Voltage
float acs712_zero_v = 1.65f; // Estimated nominal midpoint after 0.6667 divider (2.5V * 0.6667 = 1.667V)

// Calculated Real-Time Metrics
float current_temperature_c = 25.0f;
float current_vibration_rms_g = 0.05f;
float current_current_a = 0.00f;
float current_rpm = 0.0f;
bool sensor_error_flag = false;

// Alert Actuation State
bool alert_buzzer_active = false;
unsigned long alert_buzzer_duration_ms = 0;

// Sequence Counter for unique event IDs
uint32_t messageSequence = 0;

// -----------------------------------------------------------------------------
// Interrupt Service Routine for Tachometer Pulse Counter
// -----------------------------------------------------------------------------
void IRAM_ATTR onRpmPulse() {
    portENTER_CRITICAL_ISR(&mux);
    unsigned long nowUs = micros();
    // 2ms debounce to ignore optical chatter
    if (nowUs - lastPulseTime > 2000) {
        pulseCount++;
        lastPulseTime = nowUs;
    }
    portEXIT_CRITICAL_ISR(&mux);
}

// -----------------------------------------------------------------------------
// WiFi Management
// -----------------------------------------------------------------------------
void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.print("[WiFi] Connecting to SSID: ");
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WiFi] Connected successfully!");
        Serial.print("[WiFi] Assigned IP Address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n[WiFi] Connection timeout. Retrying in background...");
    }
}

// -----------------------------------------------------------------------------
// Sensor Calibration & Reading Routines
// -----------------------------------------------------------------------------
void calibrateACS712ZeroOffset() {
    Serial.println("[ACS712] Calibrating zero-current offset (motor must be stopped)...");
    uint32_t adcSum = 0;
    const int samples = 256;
    for (int i = 0; i < samples; i++) {
        adcSum += analogRead(PIN_ACS712_ADC);
        delayMicroseconds(200);
    }
    float rawAdcAvg = (float)adcSum / samples;
    acs712_zero_v = (rawAdcAvg / ESP32_ADC_RESOLUTION) * ESP32_ADC_VREF;
    Serial.print("[ACS712] Calibrated zero voltage at ESP32 pin: ");
    Serial.print(acs712_zero_v, 4);
    Serial.println(" V");
}

float readACS712Current() {
    uint32_t adcSum = 0;
    for (int i = 0; i < ACS712_SAMPLES_COUNT; i++) {
        adcSum += analogRead(PIN_ACS712_ADC);
        delayMicroseconds(100);
    }
    float rawAdcAvg = (float)adcSum / ACS712_SAMPLES_COUNT;
    float pinVoltage = (rawAdcAvg / ESP32_ADC_RESOLUTION) * ESP32_ADC_VREF;

    // Undo voltage divider to estimate actual ACS712 terminal voltage
    float acsTerminalVoltage = pinVoltage / VOLTAGE_DIVIDER_RATIO;
    float zeroTerminalVoltage = acs712_zero_v / VOLTAGE_DIVIDER_RATIO;

    // Delta from zero divided by sensitivity (0.185 V/A for 5A module)
    float currentAmps = abs(acsTerminalVoltage - zeroTerminalVoltage) / ACS712_SENSITIVITY_V_PER_A;

    // Low pass deadband filter for resting noise
    if (currentAmps < 0.03f) currentAmps = 0.0f;
    return currentAmps;
}

float calculateVibrationRMS() {
    if (!mpuInitialized) return 0.05f;

    float accZSamples[VIBE_SAMPLE_COUNT];
    float sumZ = 0.0f;

    // 1. Gather sample window
    for (int i = 0; i < VIBE_SAMPLE_COUNT; i++) {
        int16_t ax, ay, az;
        mpu.getAcceleration(&ax, &ay, &az);
        // MPU6050 default ±2g sensitivity: 16384 LSB / g
        float z_g = (float)az / 16384.0f;
        accZSamples[i] = z_g;
        sumZ += z_g;
        delayMicroseconds(VIBE_SAMPLE_DELAY_US);
    }

    // 2. Subtract DC gravity component to measure dynamic AC vibration
    float meanGravityZ = sumZ / VIBE_SAMPLE_COUNT;
    float sumSqDev = 0.0f;
    for (int i = 0; i < VIBE_SAMPLE_COUNT; i++) {
        float dev = accZSamples[i] - meanGravityZ;
        sumSqDev += (dev * dev);
    }

    // 3. Compute RMS in g
    float rms = sqrt(sumSqDev / VIBE_SAMPLE_COUNT);
    return rms;
}

void updateRpmMetric() {
    unsigned long now = millis();
    unsigned long dtMs = now - lastRpmCalculation;

    if (dtMs >= RPM_CALC_INTERVAL_MS) {
        portENTER_CRITICAL(&mux);
        unsigned long pulses = pulseCount;
        pulseCount = 0;
        portEXIT_CRITICAL(&mux);

        // Check if pulses stopped completely (motor stopped)
        if (pulses == 0 || (micros() - lastPulseTime > (RPM_TIMEOUT_MS * 1000UL))) {
            current_rpm = 0.0f;
        } else {
            // RPM = (pulses / pulsesPerRev) * (60000ms / dtMs)
            current_rpm = ((float)pulses / RPM_PULSES_PER_REV) * (60000.0f / dtMs);
        }
        lastRpmCalculation = now;
    }
}

// -----------------------------------------------------------------------------
// MQTT Message Handling & Dispatch
// -----------------------------------------------------------------------------
void onMqttMessageReceived(char* topic, byte* payload, unsigned int length) {
    Serial.print("[MQTT] Received message on topic: ");
    Serial.println(topic);

    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, payload, length);
    if (err) {
        Serial.print("[MQTT] JSON parse failure: ");
        Serial.println(err.c_str());
        return;
    }

    // Handle Alerts Triggering Physical LED/Buzzer
    if (String(topic) == TOPIC_ALERTS) {
        const char* severity = doc["severity"] | "NORMAL";
        bool actuate = doc["actuate_hardware"] | false;

        Serial.print("[Alert Callback] Severity: ");
        Serial.print(severity);
        Serial.print(" | Actuate: ");
        Serial.println(actuate ? "YES" : "NO");

        if (actuate || strcmp(severity, "CRITICAL") == 0) {
            digitalWrite(PIN_LED_ALERT, HIGH);
            digitalWrite(PIN_BUZZER, HIGH);
            alert_buzzer_active = true;
            lastAlertBuzzTime = millis();
            alert_buzzer_duration_ms = 2500; // Buzz for 2.5 seconds
        } else if (strcmp(severity, "WARNING") == 0) {
            // Warning: pulse LED only
            digitalWrite(PIN_LED_ALERT, HIGH);
            delay(100);
            digitalWrite(PIN_LED_ALERT, LOW);
        } else if (strcmp(severity, "NORMAL") == 0) {
            // Clear alert indications on recovery
            digitalWrite(PIN_LED_ALERT, LOW);
            digitalWrite(PIN_BUZZER, LOW);
            alert_buzzer_active = false;
        }
    }

    // Handle Remote Motor Commands (e.g. Stop / Reset)
    if (String(topic) == TOPIC_COMMANDS) {
        const char* command = doc["command"] | "none";
        Serial.print("[Command] Received: ");
        Serial.println(command);

        if (strcmp(command, "emergency_stop") == 0) {
            digitalWrite(PIN_L298N_ENA, LOW); // Cut motor PWM
            digitalWrite(PIN_L298N_IN1, LOW);
            digitalWrite(PIN_L298N_IN2, LOW);
            digitalWrite(PIN_LED_ALERT, HIGH);

            // Acknowledge command execution
            StaticJsonDocument<256> ack;
            ack["device_id"] = DEVICE_ID;
            ack["command"] = command;
            ack["status"] = "executed";
            ack["timestamp"] = millis();
            char ackBuf[256];
            serializeJson(ack, ackBuf);
            mqttClient.publish(TOPIC_COMMAND_ACK, ackBuf);
        }
    }
}

void reconnectMqtt() {
    if (mqttClient.connected()) return;

    Serial.print("[MQTT] Attempting broker connection to ");
    Serial.print(MQTT_BROKER_HOST);
    Serial.print(":");
    Serial.println(MQTT_BROKER_PORT);

    // Prepare Last Will & Testament (LWT)
    StaticJsonDocument<128> lwt;
    lwt["device_id"] = DEVICE_ID;
    lwt["status"] = "offline";
    lwt["reason"] = "unexpected_disconnect";
    char lwtBuf[128];
    serializeJson(lwt, lwtBuf);

    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD, TOPIC_STATUS, 1, true, lwtBuf)) {
        Serial.println("[MQTT] Connected to broker!");

        // Publish birth message
        StaticJsonDocument<128> birth;
        birth["device_id"] = DEVICE_ID;
        birth["status"] = "online";
        birth["firmware"] = "1.0.0-esp32";
        char birthBuf[128];
        serializeJson(birth, birthBuf);
        mqttClient.publish(TOPIC_STATUS, birthBuf, true);

        // Subscribe to alerts and command topics
        mqttClient.subscribe(TOPIC_ALERTS, 1);
        mqttClient.subscribe(TOPIC_COMMANDS, 1);
        Serial.println("[MQTT] Subscribed to alerts and commands.");
    } else {
        Serial.print("[MQTT] Connection failed, rc=");
        Serial.println(mqttClient.state());
    }
}

// -----------------------------------------------------------------------------
// Setup Initialization
// -----------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n=======================================================");
    Serial.println("  ESP32 Knowledge-Driven Motor Diagnostic Firmware   ");
    Serial.println("=======================================================");

    // Pin Modes
    pinMode(PIN_LED_ALERT, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    pinMode(PIN_L298N_ENA, OUTPUT);
    pinMode(PIN_L298N_IN1, OUTPUT);
    pinMode(PIN_L298N_IN2, OUTPUT);
    pinMode(PIN_IR_RPM, INPUT_PULLUP);
    pinMode(PIN_ACS712_ADC, INPUT);

    digitalWrite(PIN_LED_ALERT, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_L298N_ENA, LOW); // Safe startup with motor off

    // Attach RPM Interrupt
    attachInterrupt(digitalPinToInterrupt(PIN_IR_RPM), onRpmPulse, FALLING);

    // Initialize I2C Bus for MPU6050
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    mpu.initialize();
    if (mpu.testConnection()) {
        Serial.println("[MPU6050] Sensor connection verified successfully.");
        mpuInitialized = true;
    } else {
        Serial.println("[MPU6050] WARNING: Accelerometer connection failed. Check I2C wiring.");
        mpuInitialized = false;
        sensor_error_flag = true;
    }

    // Initialize DS18B20
    tempSensor.begin();
    int devCount = tempSensor.getDeviceCount();
    Serial.print("[DS18B20] Detected 1-Wire temperature devices: ");
    Serial.println(devCount);
    if (devCount == 0) {
        Serial.println("[DS18B20] WARNING: No temperature sensor found. Check 4.7k pullup resistor.");
        sensor_error_flag = true;
    }

    // Calibrate ACS712 Zero Point
    calibrateACS712ZeroOffset();

    // WiFi & MQTT Setup
    connectWiFi();
    mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    mqttClient.setCallback(onMqttMessageReceived);
    mqttClient.setBufferSize(512);

    Serial.println("[System] Initialization complete. Entering operational loop.");
}

// -----------------------------------------------------------------------------
// Main Operational Loop
// -----------------------------------------------------------------------------
void loop() {
    // 1. Maintain WiFi & MQTT connectivity
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }
    if (!mqttClient.connected()) {
        static unsigned long lastMqttRetry = 0;
        if (millis() - lastMqttRetry > 5000) {
            reconnectMqtt();
            lastMqttRetry = millis();
        }
    } else {
        mqttClient.loop();
    }

    // 2. Alert Buzzer Timer Management
    if (alert_buzzer_active && (millis() - lastAlertBuzzTime > alert_buzzer_duration_ms)) {
        digitalWrite(PIN_BUZZER, LOW);
        alert_buzzer_active = false;
    }

    // 3. Periodic RPM Metric Updates
    updateRpmMetric();

    // 4. Periodic Telemetry Acquisition & MQTT Publishing
    unsigned long now = millis();
    if (now - lastTelemetryPublish >= TELEMETRY_INTERVAL_MS) {
        lastTelemetryPublish = now;

        // Acquire DS18B20 Temperature
        tempSensor.requestTemperatures();
        float tempC = tempSensor.getTempCByIndex(0);
        if (tempC > -50.0f && tempC < 125.0f) {
            current_temperature_c = tempC;
        } else {
            // Sensor error reading
            sensor_error_flag = true;
        }

        // Acquire Dynamic MPU6050 Vibration RMS
        current_vibration_rms_g = calculateVibrationRMS();

        // Acquire ACS712 Motor Current
        current_current_a = readACS712Current();

        // Build Normalized Telemetry JSON
        messageSequence++;
        char eventId[48];
        snprintf(eventId, sizeof(eventId), "%s-esp-%lu-%lu", DEVICE_ID, now / 1000, messageSequence);

        StaticJsonDocument<384> doc;
        doc["event_id"] = eventId;
        doc["device_id"] = DEVICE_ID;
        doc["timestamp"] = now; // Milliseconds uptime or ISO if NTP synchronized
        doc["source"] = "esp32_hardware";
        doc["temperature_c"] = round(current_temperature_c * 10.0f) / 10.0f;
        doc["vibration_rms_g"] = round(current_vibration_rms_g * 1000.0f) / 1000.0f;
        doc["current_a"] = round(current_current_a * 100.0f) / 100.0f;
        doc["rpm"] = round(current_rpm * 10.0f) / 10.0f;
        doc["sensor_status"] = sensor_error_flag ? "sensor_fault" : "ok";

        char jsonBuffer[384];
        size_t len = serializeJson(doc, jsonBuffer);

        if (mqttClient.connected()) {
            mqttClient.publish(TOPIC_SENSORS, jsonBuffer);
            Serial.print("[Telemetry Publish] ");
            Serial.println(jsonBuffer);
        } else {
            Serial.print("[Telemetry Local Offline] ");
            Serial.println(jsonBuffer);
        }
    }
}
