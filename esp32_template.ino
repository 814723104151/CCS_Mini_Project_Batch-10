/*
 * esp32_template.ino
 * IoT Device Secure Communication using Lightweight ECC
 * 
 * Outline:
 * 1. Generate or load ECC key pair (secp256r1)
 * 2. Use ECDH with server public key to derive shared secret
 * 3. Derive AES-GCM key using HKDF (SHA256)
 * 4. Encrypt sensor data and publish over MQTT
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Replace with your credentials
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";
const char* mqtt_server = "BROKER_IP";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected!");
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) reconnect();

  // Read dummy sensor values
  float temp = random(20, 30);
  float hum = random(40, 60);

  // (Pseudo) ECC + AES encryption logic here
  // Use mbedTLS or micro-ecc to implement ECDH + AES-GCM

  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["temperature"] = temp;
  doc["humidity"] = hum;
  doc["device"] = "ESP32-Node";

  char buffer[256];
  serializeJson(doc, buffer);

  // Publish encrypted payload (replace with actual encryption)
  client.publish("iot/ecc/encrypted", buffer);
  Serial.println("Sent encrypted message!");
  delay(5000);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32Client")) {
      client.subscribe("iot/ecc/encrypted");
    } else {
      delay(5000);
    }
  }
}
