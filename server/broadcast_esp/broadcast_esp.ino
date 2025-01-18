#include "esp_now.h"
#include "WiFi.h"
#include <string.h>

#define PLAYER_COUNT 2
#define BAUD_RATE 115200

// Array of MAC addresses for each player
uint8_t addresses[PLAYER_COUNT][6] = {
  {0x34, 0x5F, 0x45, 0xA9, 0x8D, 0x08},  // Address B
  {0x14, 0x2B, 0x2F, 0xC5, 0x86, 0x80}, // Address A
};

char playerIds[PLAYER_COUNT][32] = {"player1", "player2"};

// Struct to hold bot data
typedef struct broadcast_data {
  char botId[32];  // Unique ID for the bot
  int v;            // X velocity
  int w;            // Z rotation
} broadcast_data;

typedef struct bot_data {
  char botId[32];
  int ldrVal;
} bot_data;

broadcast_data myData;
esp_now_peer_info_t peerInfo;

void onDataSent(const uint8_t *macAddr, esp_now_send_status_t status) {
  // Serial.print("Last Packet Send Status:\t");
  // Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
}

void onDataRecv(const esp_now_recv_info_t *recvInfo, const uint8_t *incomingData, int len) {
  bot_data receivedData;
  memcpy(&receivedData, incomingData, sizeof(receivedData));
  
  Serial.print("{\"id\": \"");
  Serial.print(receivedData.botId);
  Serial.print("\", \"ldr\": ");
  Serial.print(receivedData.ldrVal);
  Serial.print(", \"succ\": 1}");
  Serial.println();
}

void setup() {
  Serial.begin(BAUD_RATE);
  while (!Serial) {
    // Wait for serial port to connect (needed for some boards like ESP32)
  }

  WiFi.mode(WIFI_MODE_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Serial.println("ESP is ready to receive data.");

  // Register callback for sending data
  esp_now_register_send_cb(onDataSent);
  esp_now_register_recv_cb(onDataRecv);

  // Add peers
  for (int i = 0; i < sizeof(addresses) / sizeof(addresses[0]); i++) {
    memcpy(peerInfo.peer_addr, addresses[i], 6);
    peerInfo.channel = 0; // Default channel
    peerInfo.encrypt = false;

    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
      Serial.println("{\"succ\": 0}");
    }
  }
}

void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n');  // Read data until newline

    String player_id = getValueFromJson(incomingData, "player_id");
    String v_str = getValueFromJson(incomingData, "v");
    String w_str = getValueFromJson(incomingData, "w");

    int v, w;
    int macIndex = getMacAddress(player_id.c_str()); // Convert String to C-string

    sscanf(v_str.c_str(), "%d", &v);
    sscanf(w_str.c_str(), "%d", &w);

    if (macIndex != -1) {
      strncpy(myData.botId, player_id.c_str(), sizeof(myData.botId));
      myData.v = v;
      myData.w = w;

      // Send data to the selected peer
      esp_err_t result = esp_now_send(addresses[macIndex], (uint8_t *)&myData, sizeof(myData));
      if (result != ESP_OK) {
        Serial.println("{\"succ\": 0}");
      }
    } else {
      Serial.println("{\"succ\": 0}");
    }
  }

  delay(100);
}

// Function to extract a value from a JSON-like string (key: value pairs)
String getValueFromJson(String json, String key) {
  // Find the key in the JSON string
  int keyIndex = json.indexOf(key);
  if (keyIndex == -1) {
    return "";  // Return empty string if the key is not found
  }

  // Find the position of the colon and the comma or closing brace after the key
  int startIdx = json.indexOf(":", keyIndex) + 1;
  int endIdx = json.indexOf(",", startIdx);
  if (endIdx == -1) {
    // If there's no comma, the value ends with the closing brace
    endIdx = json.indexOf("}", startIdx);
  }

  // Extract the value and trim any extra spaces
  String value = json.substring(startIdx, endIdx);
  value.trim();  // Remove leading and trailing spaces
  
  // Remove quotes if they exist
  if (value.startsWith("\"") && value.endsWith("\"")) {
    value = value.substring(1, value.length() - 1);
  }

  return value;
}

// Function to get the MAC address index for a player_id
int getMacAddress(const char player_id[32]) {
  for (int i = 0; i < PLAYER_COUNT; i++) {
    if (strcmp(playerIds[i], player_id) == 0) {
      return i;  // Return the index if player_id matches
    }
  }
  return -1;  // Return -1 if player_id not found
}
