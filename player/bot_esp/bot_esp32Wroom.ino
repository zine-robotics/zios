#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>

// Motor A (Left Motor)
const int motor1Pin1 = 32;  // L293D Input 1
const int motor1Pin2 = 33;  // L293D Input 2
const int enableMotor1 = 5; // L293D Enable 1

// Motor B (Right Motor)
const int motor2Pin1 = 13;   // L293D Input 3
const int motor2Pin2 = 12;   // L293D Input 4
const int enableMotor2 = 14; // L293D Enable 2

float wheelBase = 2;
float baseSpeed = 100;
char currentBotId[32] = "2";

// Define peer addresses
uint8_t addresses[][6] = {
    //    {0x94, 0x54, 0xc5, 0xA9, 0xa2, 0xf8},
    {0x14, 0x33, 0x5c, 0x02, 0xf9, 0x54},
    //{0xbc, 0xdd, 0xc2, 0x79, 0xf2, 0x99},
    // 94:54:c5:a9:a2:f8

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

    int leftPWM = constrain(map(leftSpeed, -25, 25, -255, 255), -255, 255);
    int rightPWM = constrain(map(rightSpeed, -25, 25, -255, 255), -255, 255);

    Serial.printf("Control Motors - Left PWM: %d, Right PWM: %d\n", leftPWM, rightPWM);

    if (leftPWM > 0)
    {
        analogWrite(motor1Pin1, leftPWM);
        analogWrite(motor1Pin2, 0);
    }
    else
    {
        analogWrite(motor1Pin1, 0);
        analogWrite(motor1Pin2, abs(leftPWM));
    }

    if (rightPWM > 0)
    {
        analogWrite(motor2Pin1, rightPWM);
        analogWrite(motor2Pin2, 0);
    }
    else
    {
        analogWrite(motor2Pin1, 0);
        analogWrite(motor2Pin2, abs(rightPWM));
    }
    delay(100);
}

void stopMotor()
{
    //  Serial.println("Forward");
    analogWrite(motor1Pin1, 0);
    analogWrite(motor1Pin2, 0);
    analogWrite(motor2Pin1, 0);
    analogWrite(motor2Pin2, 0);
    delay(10);
}

void onDataReceive(const esp_now_recv_info_t *recvInfo, const uint8_t *data, int len)
{
    if (len == sizeof(broadcast_data))
    {
        memcpy(&broadcastData, data, sizeof(broadcast_data));

        // Get sender MAC
        char macStr[18];
        snprintf(macStr, sizeof(macStr),
                 "%02X:%02X:%02X:%02X:%02X:%02X",
                 recvInfo->src_addr[0], recvInfo->src_addr[1], recvInfo->src_addr[2],
                 recvInfo->src_addr[3], recvInfo->src_addr[4], recvInfo->src_addr[5]);

        Serial.printf("Received Data from %s - Bot ID: %s, v: %d, w: %d\n",
                      macStr, broadcastData.botId, broadcastData.v, broadcastData.w);

        controlMotors(broadcastData.v, broadcastData.w);

        stopMotor();
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.println("Starting ESP-NOW...");

    WiFi.mode(WIFI_STA);
    if (esp_now_init() != ESP_OK)
    {
        Serial.println("ESP-NOW Initialization Failed");
        return;
    }

    esp_now_register_recv_cb(onDataReceive);

    for (int i = 0; i < sizeof(addresses) / sizeof(addresses[0]); i++)
    {
        esp_now_peer_info_t peerInfo = {};
        memcpy(peerInfo.peer_addr, addresses[i], 6);
        peerInfo.channel = 0;
        peerInfo.encrypt = false;

        if (esp_now_add_peer(&peerInfo) != ESP_OK)
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

void loop()
{
    analogWrite(motor1Pin1, 150);
    analogWrite(motor1Pin2, 0);
    analogWrite(motor2Pin1, 150);
    analogWrite(motor2Pin2, 0);
    delay(100);
}