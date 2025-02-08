#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <espnow.h>

// Motor A (Left Motor)
const int motor1Pin1 = 13;   // GPIO14 (D6) - L293D Input 1
const int motor1Pin2 = 12;   // GPIO12 (D7) - L293D Input 2
const int enableMotor1 = 15; // GPIO13 (D8) - L293D Enable 1

// Motor B (Right Motor)
const int motor2Pin1 = 0;   // GPIO0 (D3) - L293D Input 3
const int motor2Pin2 = 4;   // GPIO4 (D2) - L293D Input 4
const int enableMotor2 = 2; // GPIO2 (D4) - L293D Enable 2

float wheelBase = 2;
float baseSpeed = 100;
char currentBotId[32] = "3";

// Define peer addresses
uint8_t addresses[][6] = {
    {0x94, 0x54, 0xc5, 0xA9, 0xa7, 0xa4},
};

// Struct for received data
typedef struct
{
    char botId[32];
    int v; // Linear velocity
    int w; // Angular velocity
} broadcast_data;

broadcast_data broadcastData;

void controlMotors(int v, int w)
{
    float leftSpeed = v - (w * wheelBase / 2.0);
    float rightSpeed = v + (w * wheelBase / 2.0);

    int leftPWM = constrain(map(leftSpeed, -25, 25, -1023, 1023), -1023, 1023);
    int rightPWM = constrain(map(rightSpeed, -25, 25, -1023, 1023), -1023, 1023);

    Serial.print("Control Motors - Left PWM: ");
    Serial.print(leftPWM);
    Serial.print(" Right PWM: ");
    Serial.println(rightPWM);

    if (leftPWM > 0)
    {
        analogWrite(motor1Pin1, leftPWM);
        analogWrite(motor1Pin2, 0);
    }
    else if (leftPWM < 0)
    {
        analogWrite(motor1Pin1, 0);
        analogWrite(motor1Pin2, -leftPWM);
    }
    else
    {
        analogWrite(motor1Pin1, 0);
        analogWrite(motor1Pin2, 0);
    }

    if (rightPWM > 0)
    {
        analogWrite(motor2Pin1, rightPWM);
        analogWrite(motor2Pin2, 0);
    }
    else if (rightPWM < 0)
    {
        analogWrite(motor2Pin1, 0);
        analogWrite(motor2Pin2, -rightPWM);
    }
    else
    {
        analogWrite(motor2Pin1, 0);
        analogWrite(motor2Pin2, 0);
    }

    delay(100);
}

void onDataReceive(uint8_t *mac, uint8_t *data, uint8_t len)
{
    if (len == sizeof(broadcast_data))
    {
        memcpy(&broadcastData, data, sizeof(broadcast_data));
        Serial.print("Received Data - Bot ID: ");
        Serial.print(broadcastData.botId);
        Serial.print(" v: ");
        Serial.print(broadcastData.v);
        Serial.print(" w: ");
        Serial.println(broadcastData.w);
        controlMotors(broadcastData.v, broadcastData.w);
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.println("Starting ESP-NOW...");

    WiFi.mode(WIFI_STA);
    if (esp_now_init() != 0)
    {
        Serial.println("ESP-NOW Initialization Failed");
        return;
    }

    esp_now_set_self_role(ESP_NOW_ROLE_SLAVE);
    esp_now_register_recv_cb(onDataReceive);

    for (int i = 0; i < sizeof(addresses) / sizeof(addresses[0]); i++)
    {
        if (esp_now_add_peer(addresses[i], ESP_NOW_ROLE_CONTROLLER, 1, NULL, 0) != 0)
        {
            Serial.println("Failed to add peer");
        }
    }

    pinMode(motor1Pin1, OUTPUT);
    pinMode(motor1Pin2, OUTPUT);
    pinMode(enableMotor1, OUTPUT);
    pinMode(motor2Pin1, OUTPUT);
    pinMode(motor2Pin2, OUTPUT);
    pinMode(enableMotor2, OUTPUT);

    digitalWrite(enableMotor1, HIGH);
    digitalWrite(enableMotor2, HIGH);
}

void MoveForward()
{
    //  Serial.println("Forward");
    digitalWrite(motor1Pin1, LOW);
    digitalWrite(motor1Pin2, HIGH);
    analogWrite(enableMotor1, 200);

    digitalWrite(motor2Pin1, LOW);
    digitalWrite(motor2Pin2, HIGH);

    analogWrite(enableMotor2, 200);
    delay(100);
}

void loop()
{

    //   MoveForward();
    //  controlMotors(-1,0);
    //  controlMotors(0,1);
    //  controlMotors(0,-1);

    // No need for loop code as ESP-NOW runs via interrupt callbacks
}