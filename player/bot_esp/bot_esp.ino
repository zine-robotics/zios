#include "esp_now.h"
#include "WiFi.h"

// Define peer addresses
uint8_t addresses[][6] = {
    {0x94, 0x54, 0xc5, 0xA9, 0xa7, 0xa4},
};


float wheelBase = 2;
// Motor pins
const int leftMotorPin1 = 13;
const int leftMotorPin2 = 12;
const int rightMotorPin1 = 14;
const int rightMotorPin2 = 27;
const int LDR_PIN = 32;
//// LDR pin
//#define LDR_PIN  A26

// Motor speed variables
int v = 1;  // Linear velocity
int w = 1;  // Angular velocity
char currentBotId[32] = "player1";

// Struct for received data (broadcast data)
typedef struct broadcast_data {
  char botId[32];  // Bot ID (max 32 characters)
  int v;           // Linear velocity
  int w;           // Angular velocity
} broadcast_data;

// Struct for sent data (bot data)
typedef struct bot_data {
  char botId[32];  // Bot ID (max 32 characters)
  int ldrValue;    // LDR sensor value
} bot_data;

// Variables for struct instances
broadcast_data broadcastData;
bot_data botData;

esp_now_peer_info_t peerInfo;

// Callback for when data is sent
void onDataSent(const uint8_t *macAddr, esp_now_send_status_t status) {
//  Serial.print("Data Sent to ");
//  for (int i = 0; i < 6; i++) {
//    Serial.printf("%02X:", macAddr[i]);
//  }
//  Serial.print(" Status: ");
//  if (status == ESP_NOW_SEND_SUCCESS) {
//    Serial.println("Success");
//  } else {
//    Serial.println("Failed");
//  }
}

// Callback for when data is received
void onDataReceive(const esp_now_recv_info_t* recvInfo, const uint8_t *data, int len) {
  if (len == sizeof(broadcast_data)) {
    memcpy(&broadcastData, data, sizeof(broadcast_data));

    // Serial log for received data
    Serial.print("Received Data - Bot ID: ");
    Serial.print(broadcastData.botId);
    Serial.print(" v: ");
    Serial.print(broadcastData.v);
    Serial.print(" w: ");
    Serial.println(broadcastData.w);

    // Control motors based on received data
    controlMotors(broadcastData.v, broadcastData.w);


  }
}


void setup() {
  // Start the Serial communication for debugging
  Serial.begin(115200);
  Serial.println("Starting ESP-NOW...");

  // Initialize the bot ID
  strncpy(botData.botId, currentBotId, sizeof(botData.botId));

  // Initialize WiFi in Station mode
  WiFi.mode(WIFI_MODE_STA);

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW Initialization Failed");
    return;
  }

  // Register callback for when data is sent
  esp_now_register_send_cb(onDataSent);
  esp_now_register_recv_cb(onDataReceive);

  // Add peer information
  for (int i = 0; i < sizeof(addresses) / sizeof(addresses[0]); i++) {
    memcpy(peerInfo.peer_addr, addresses[i], 6);
    peerInfo.channel = 0;  // Default channel
    peerInfo.encrypt = false;

    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
      Serial.println("Failed to add peer");
      return;
    }
  }

  // Set motor pins as outputs
  pinMode(leftMotorPin1, OUTPUT);
  pinMode(leftMotorPin2, OUTPUT);
  pinMode(rightMotorPin1, OUTPUT);
  pinMode(rightMotorPin2, OUTPUT);

  // Set LDR pin as input
  digitalWrite(35, 1);

}

  void controlMotors(int v, int w) {
    float leftSpeed = v - (w * wheelBase / 2.0);
    float rightSpeed = v + (w * wheelBase / 2.0);

 // Map the speeds from their range (-10 to 10) to PWM range (-255 to 255)
    int leftPWM = constrain(map(leftSpeed, -25, 25, -255, 255), -255, 255);
    int rightPWM = constrain(map(rightSpeed, -25, 25, -255, 255), -255, 255);
 // Serial logs for motor control
    Serial.print("Control Motors - Left PWM: ");
    Serial.print(leftPWM);
    Serial.print(" Right PWM: ");
    Serial.println(rightPWM);

  if (leftPWM > 0) {
    analogWrite(leftMotorPin1, leftPWM);
    analogWrite(leftMotorPin2, 0);
  } else {
    analogWrite(leftMotorPin1, 0);
    analogWrite(leftMotorPin2, -leftPWM);
  }

  if (rightPWM > 0) {
    analogWrite(rightMotorPin1, rightPWM);
    analogWrite(rightMotorPin2, 0);
  } else {
    analogWrite(rightMotorPin1, 0);
    analogWrite(rightMotorPin2, -rightPWM);
  }

  delay(100);
}


void loop() {
  // Continuously read LDR value and send data
  int ldrValue = analogRead(LDR_PIN);
  botData.ldrValue = ldrValue;

  // Serial log for LDR value
  Serial.print("LDR Value: ");
  Serial.println(ldrValue);

  // Send only botId and ldrValue
  esp_err_t result = esp_now_send(addresses[0], (uint8_t *)&botData, sizeof(botData));
  delay(100);
//  if (result == ESP_OK) {
//    Serial.println("LDR Data Sent Successfully");
//  } else {
//    Serial.println("Error in Sending LDR Data");
//  }
  
}