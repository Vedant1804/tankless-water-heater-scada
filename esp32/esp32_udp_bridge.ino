/*
================================================================================
ESP32 SERIAL-TO-UDP INDUSTRIAL BRIDGE FOR TANKLESS WATER HEATER MONITORING
================================================================================
Architecture:
  Simulink Model (Laptop) 
      -> USB Serial (115200 baud) 
      -> ESP32 (Receives via Serial)
      -> Wi-Fi UDP (Port 5005)
      -> Python SCADA Dashboard (Laptop)

Payload Format:
  outlet_temperature,flow_rate,burner_power,heat_cell_temperature\n
  Example: 48.08,5.00,13.20,48.10
================================================================================
*/

#include <WiFi.h>
#include <WiFiUdp.h>

// =============================================================================
// USER CONFIGURATION (UPDATE THESE FOR YOUR NETWORK)
// =============================================================================
const char* WIFI_SSID     = "YOUR_WIFI_NAME";        // Wi-Fi SSID / Hotspot Name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";    // Wi-Fi Password

// Laptop IP Address running the Streamlit Dashboard
// (Find using 'ipconfig' in Windows Command Prompt, e.g. 192.168.1.50)
const char* LAPTOP_IP     = "192.168.1.100";
const int   UDP_PORT      = 5005;                    // Must match dashboard port

// Hardware Configuration
const int   SERIAL_BAUD   = 115200;                  // Baud rate matching Simulink
const int   LED_PIN       = 2;                       // Onboard status LED (GPIO 2)

// Set to 1 to enable standalone hardware simulation (tests Wi-Fi UDP without Simulink)
// Set to 0 for production mode (reads live serial data from Simulink)
#define TEST_GENERATOR_MODE 0

// =============================================================================
// GLOBAL OBJECTS
// =============================================================================
WiFiUDP udp;
char serialBuffer[128];
int bufferIndex = 0;
unsigned long lastPacketMillis = 0;
unsigned long lastBlinkMillis = 0;

// Test generator variables (only used if TEST_GENERATOR_MODE == 1)
float sim_outlet = 48.08;
float sim_flow = 5.00;
float sim_power = 13.20;
float sim_cell = 48.10;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(SERIAL_BAUD);
  delay(1000);

  Serial.println("\n========================================================");
  Serial.println("   ESP32 SCADA TELEMETRY BRIDGE - TANKLESS WATER HEATER");
  Serial.println("========================================================");

  // Connect to Wi-Fi
  connectWiFi();

  // Start UDP
  udp.begin(UDP_PORT);
  Serial.printf("[UDP] Listening on local port: %d\n", UDP_PORT);
  Serial.printf("[UDP] Forwarding packets to: %s:%d\n", LAPTOP_IP, UDP_PORT);

#if TEST_GENERATOR_MODE
  Serial.println("[MODE] TEST GENERATOR ACTIVE - Emulating process packets @ 2Hz");
#else
  Serial.println("[MODE] LIVE RELAY ACTIVE - Awaiting serial data from Simulink");
#endif
  Serial.println("========================================================\n");
}

void loop() {
  // Ensure Wi-Fi remains connected
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

#if TEST_GENERATOR_MODE
  // Autonomous packet generator for testing Wi-Fi communication without Simulink
  if (millis() - lastPacketMillis >= 500) { // 2 Hz transmission
    lastPacketMillis = millis();

    // Small physical oscillations
    sim_flow = 5.00 + 0.15 * sin(millis() / 2000.0);
    sim_power = 13.20 + 0.25 * sin(millis() / 1500.0);
    sim_cell = 48.10 + 0.10 * sin(millis() / 3000.0);
    sim_outlet = 48.08 + 0.08 * sin(millis() / 3500.0);

    char payload[64];
    snprintf(payload, sizeof(payload), "%.2f,%.2f,%.2f,%.2f\n",
             sim_outlet, sim_flow, sim_power, sim_cell);

    sendUDP(payload);
    Serial.printf("[TX TEST] %s", payload);
  }

#else
  // Production Serial Receiver: Read characters from Simulink Serial Send block
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (bufferIndex > 0) {
        serialBuffer[bufferIndex] = '\0'; // Null-terminate string
        
        // Validate minimum sanity (must contain 3 commas for 4 values)
        int commaCount = 0;
        for (int i = 0; i < bufferIndex; i++) {
          if (serialBuffer[i] == ',') commaCount++;
        }

        if (commaCount >= 3) {
          sendUDP(serialBuffer);
          // Visual heartbeat blink
          digitalWrite(LED_PIN, HIGH);
          lastBlinkMillis = millis();
        } else {
          Serial.printf("[WARN] Ignored malformed serial line: %s\n", serialBuffer);
        }

        bufferIndex = 0; // Reset buffer
      }
    } else {
      if (bufferIndex < sizeof(serialBuffer) - 1) {
        serialBuffer[bufferIndex++] = c;
      } else {
        // Buffer overflow protection: reset
        bufferIndex = 0;
      }
    }
  }
#endif

  // Turn off heartbeat LED after 40ms pulse
  if (millis() - lastBlinkMillis > 40) {
    digitalWrite(LED_PIN, LOW);
  }
}

// Send UDP Datagram to laptop
void sendUDP(const char* message) {
  udp.beginPacket(LAPTOP_IP, UDP_PORT);
  udp.write((const uint8_t*)message, strlen(message));
  udp.endPacket();
}

// Connect or reconnect to Wi-Fi network
void connectWiFi() {
  Serial.printf("[WIFI] Connecting to SSID: %s ", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Flash LED during connect
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(LED_PIN, LOW);
    Serial.println("\n[WIFI] Connected successfully!");
    Serial.printf("[WIFI] ESP32 Assigned IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[WIFI] ESP32 MAC Address: %s\n", WiFi.macAddress().c_str());
    Serial.printf("[WIFI] RSSI Signal: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("\n[ERROR] Wi-Fi connection timed out. Retrying in background...");
  }
}
