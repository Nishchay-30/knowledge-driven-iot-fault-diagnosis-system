
#include <WiFi.h>
#include "secrets.h"
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <time.h>
#include <math.h>

// ===== WIFI & HIVEMQ CREDENTIALS =====

const char* MQTT_HOST =
  "1285e2f1b7e14c249b55489e3f2de0e3.s1.eu.hivemq.cloud";

const uint16_t MQTT_PORT = 8883;

const char* MQTT_TOPIC = "iot/factory/motor01/sensors";

// ===== ESP32 PIN CONNECTIONS =====
#define TEMP_PIN 18
#define ACS_PIN 34
#define IR_PIN 27
#define IN1 25
#define IN2 26

// ===== SENSOR SETTINGS =====
const float ACS_SENSITIVITY = 0.100f;
const float DIVIDER_RATIO = 3.2f;
const uint32_t PULSES_PER_REV = 1;

const unsigned long PUBLISH_MS = 1000;
const unsigned long MOTOR_LIMIT_MS = 3000;

// ===== VERIFIED ISRG ROOT X1 CERTIFICATE =====
static const char ROOT_CA[] = R"CERT(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
)CERT";

// ===== CLIENTS =====
WiFiClientSecure secureClient;
PubSubClient mqttClient(secureClient);

OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

// ===== RPM COUNTER =====
volatile uint32_t pulseCount = 0;
volatile uint32_t lastPulseUs = 0;

portMUX_TYPE rpmMux = portMUX_INITIALIZER_UNLOCKED;

// ===== STATE =====
float zeroVoltage = 2.5f;
bool motorOn = false;

unsigned long motorStarted = 0;
unsigned long lastPublish = 0;
unsigned long lastRPMRead = 0;
unsigned long lastMQTTAttempt = 0;
unsigned long lastWiFiAttempt = 0;
unsigned long lastTimeMessage = 0;

// ===== IR SENSOR INTERRUPT =====
void IRAM_ATTR onIRPulse() {
  uint32_t now = micros();

  portENTER_CRITICAL_ISR(&rpmMux);

  if ((uint32_t)(now - lastPulseUs) > 3000) {
    pulseCount++;
    lastPulseUs = now;
  }

  portEXIT_CRITICAL_ISR(&rpmMux);
}

// ===== READ ACS712 VOLTAGE =====
float readACSVoltage() {
  float sumMilliVolts = 0;

  for (int i = 0; i < 150; i++) {
    sumMilliVolts += analogReadMilliVolts(ACS_PIN);
    delay(2);
  }

  return (sumMilliVolts / 150.0f / 1000.0f)
         * DIVIDER_RATIO;
}

// ===== MOTOR CONTROL =====
void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  motorOn = false;
  Serial.println("MOTOR OFF");
}

void startMotor() {
  if (motorOn) return;

  motorStarted = millis();

  digitalWrite(IN2, LOW);
  digitalWrite(IN1, HIGH);

  motorOn = true;
  Serial.println("MOTOR ON (max 3 seconds)");
}

// ===== WIFI CONNECTION =====
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setAutoReconnect(true);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi");

  unsigned long begun = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - begun < 15000) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi Connected! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi not connected; will retry.");
  }
}

// ===== HIVEMQ CONNECTION =====
void connectMQTT() {
  if (mqttClient.connected() || motorOn) return;

  Serial.println(
    "Connecting to HiveMQ Cloud (TLS 8883)..."
  );

  Serial.print("Free heap: ");
  Serial.println(ESP.getFreeHeap());

  IPAddress brokerIP;

  if (!WiFi.hostByName(MQTT_HOST, brokerIP)) {
    Serial.println("DNS lookup failed for MQTT hostname.");
    return;
  }

  Serial.print("Broker IP: ");
  Serial.println(brokerIP);

  String clientId = "motor01-";
  clientId += String((uint32_t)ESP.getEfuseMac(), HEX);

  if (mqttClient.connect(
        clientId.c_str(),
        MQTT_USER,
        MQTT_PASSWORD)) {

    Serial.println("MQTT CONNECTED!");

  } else {
    Serial.print("MQTT Failed. State: ");
    Serial.println(mqttClient.state());

    char sslError[160] = {0};

    int errorCode = secureClient.lastError(
      sslError,
      sizeof(sslError)
    );

    Serial.print("TLS Error Code: ");
    Serial.println(errorCode);

    Serial.print("TLS Error: ");
    Serial.println(sslError);

    secureClient.stop();
  }
}

// ===== SENSOR DATA AND MQTT PUBLISH =====
void publishReadings() {
  tempSensor.requestTemperatures();

  float temperature =
    tempSensor.getTempCByIndex(0);

  bool temperatureValid =
    temperature != DEVICE_DISCONNECTED_C &&
    temperature > -55.0f &&
    temperature < 125.0f;

  float sensorV = readACSVoltage();

  float currentA = fabsf(
    (sensorV - zeroVoltage) / ACS_SENSITIVITY
  );

  unsigned long now = millis();
  unsigned long elapsed = now - lastRPMRead;

  portENTER_CRITICAL(&rpmMux);

  uint32_t pulses = pulseCount;
  pulseCount = 0;

  portEXIT_CRITICAL(&rpmMux);

  lastRPMRead = now;

  float rpm = elapsed > 0
    ? pulses * 60000.0f /
      (elapsed * PULSES_PER_REV)
    : 0.0f;

  // Temperature JSON
  char tempValue[20];

  if (temperatureValid) {
    snprintf(
      tempValue,
      sizeof(tempValue),
      "%.2f",
      temperature
    );
  } else {
    strcpy(tempValue, "null");
  }

  // UTC time
  time_t epoch = time(nullptr);
  struct tm utc;
  gmtime_r(&epoch, &utc);

  char timestamp[30];

  strftime(
    timestamp,
    sizeof(timestamp),
    "%Y-%m-%dT%H:%M:%SZ",
    &utc
  );

  // MQTT JSON payload
  char payload[480];

  int len = snprintf(
    payload,
    sizeof(payload),

    "{\"device_id\":\"motor01\","
    "\"location\":\"factory_line_01\","
    "\"timestamp\":\"%s\","
    "\"machine_status\":\"%s\","
    "\"motor_status\":\"%s\","
    "\"sensors\":{"
    "\"temperature_c\":%s,"
    "\"current_a\":%.3f,"
    "\"rpm\":%.1f}}",

    timestamp,
    motorOn ? "RUNNING" : "STOPPED",
    motorOn ? "ON" : "OFF",
    tempValue,
    currentA,
    rpm
  );

  if (len < 0 || len >= (int)sizeof(payload)) {
    Serial.println("Error: JSON payload too large.");
    return;
  }

  Serial.print("Temperature: ");

  if (temperatureValid) {
    Serial.println(temperature, 2);
  } else {
    Serial.println("SENSOR ERROR");
  }

  Serial.print("Current (approx A): ");
  Serial.println(currentA, 3);

  Serial.print("RPM (approx): ");
  Serial.println(rpm, 1);

  Serial.print("Motor command: ");
  Serial.println(motorOn ? "ON" : "OFF");

  if (mqttClient.publish(MQTT_TOPIC, payload)) {
    Serial.print("MQTT PUBLISHED: ");
    Serial.println(payload);
  } else {
    Serial.print("MQTT publish failed, state: ");
    Serial.println(mqttClient.state());
  }
}

// ===== SETUP =====
void setup() {
  // Motor OFF at startup
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  Serial.begin(115200);
  delay(500);

  Serial.println(
    "ESP32 Knowledge-Driven IoT Fault Diagnosis"
  );

  pinMode(IR_PIN, INPUT);

  attachInterrupt(
    digitalPinToInterrupt(IR_PIN),
    onIRPulse,
    FALLING
  );

  tempSensor.begin();

Serial.print("DS18B20 Sensors Found: ");
Serial.println(tempSensor.getDeviceCount());


  analogReadResolution(12);
  analogSetPinAttenuation(ACS_PIN, ADC_11db);

  zeroVoltage = readACSVoltage();
  lastRPMRead = millis();

  Serial.print("ACS712 zero offset: ");
  Serial.println(zeroVoltage, 3);

  // Secure HiveMQ connection
  secureClient.setCACert(ROOT_CA);
  secureClient.setTimeout(10);

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setBufferSize(768);
  mqttClient.setSocketTimeout(5);
  mqttClient.setKeepAlive(30);

  connectWiFi();

  configTime(
    0, 0,
    "time.google.com",
    "time.cloudflare.com",
    "pool.ntp.org"
  );

  Serial.println("Commands:");
  Serial.println("1 = Run motor for 10 seconds");
  Serial.println("0 = Stop motor");
  Serial.println("z = Zero-current calibration");
}

// ===== MAIN LOOP =====
void loop() {
  if (Serial.available()) {
    char command = Serial.read();

    if (command == '0') {
      stopMotor();
    }

    if (command == '1') {
      startMotor();
    }

    if (command == 'z' && !motorOn) {
      zeroVoltage = readACSVoltage();

      Serial.print("New ACS712 zero offset: ");
      Serial.println(zeroVoltage, 3);
    }
  }

  // Automatic motor stop
  if (motorOn &&
      millis() - motorStarted >= MOTOR_LIMIT_MS) {
    stopMotor();
  }

  // WiFi reconnect
  if (WiFi.status() != WL_CONNECTED) {
    if (motorOn) stopMotor();

    if (millis() - lastWiFiAttempt >= 10000) {
      lastWiFiAttempt = millis();

      Serial.println("Reconnecting WiFi...");
      WiFi.reconnect();
    }

    delay(20);
    return;
  }

  // Time sync for secure TLS
  if (time(nullptr) < 1700000000) {
    if (millis() - lastTimeMessage >= 5000) {
      lastTimeMessage = millis();
      Serial.println("Waiting for NTP time sync...");
    }

    delay(20);
    return;
  }

  // MQTT reconnect
  if (!mqttClient.connected()) {
    if (motorOn) stopMotor();

    if (millis() - lastMQTTAttempt >= 5000) {
      lastMQTTAttempt = millis();
      connectMQTT();
    }
  }

  mqttClient.loop();

  // Publish sensor readings every 5 seconds
  if (mqttClient.connected() &&
      millis() - lastPublish >= PUBLISH_MS) {

    lastPublish = millis();
    publishReadings();
  }

  if (motorOn &&
      millis() - motorStarted >= MOTOR_LIMIT_MS) {
    stopMotor();
  }

  delay(10);
}
