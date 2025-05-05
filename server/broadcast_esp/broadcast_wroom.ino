extern "C"
{
#include <espnow.h>
#include <user_interface.h>
}
#include <ESP8266WiFi.h>

#define PLAYER_COUNT 2
#define BAUD_RATE 115200

uint8_t addresses[PLAYER_COUNT][6] = {
    {0x48, 0x3f, 0xda, 0x62, 0xa0, 0xbb},
    //  {0x14, 0x2b, 0x2f, 0xc5, 0x86, 0x80},
    {0x94, 0x54, 0xc5, 0xA9, 0xa2, 0xf8},
    // {0x94, 0x54, 0xc5, 0xA9, 0xa7, 0xa4},
};

char playerIds[PLAYER_COUNT][32] = {"2", "1"};

typedef struct broadcast_data
{
    char botId[32];
    int v;
    int w;
} broadcast_data;

typedef struct bot_data
{
    char botId[32];
    int ldrVal;
} bot_data;

broadcast_data myData;

// Callback when data is sent
void onDataSent(uint8_t *mac_addr, uint8_t sendStatus)
{
    // No-op or debug
}

// Callback when data is received
void onDataRecv(uint8_t *mac_addr, uint8_t *incomingData, uint8_t len)
{
    bot_data receivedData;
    memcpy(&receivedData, incomingData, sizeof(receivedData));

    Serial.print("{\"id\": \"");
    Serial.print(receivedData.botId);
    Serial.print("\", \"ldr\": ");
    Serial.print(receivedData.ldrVal);
    Serial.print(", \"succ\": 1}");
    Serial.println();
}

void setup()
{
    Serial.begin(BAUD_RATE);
    WiFi.mode(WIFI_STA);
    wifi_set_opmode(STATION_MODE); // Legacy for ESP8266

    if (esp_now_init() != 0)
    {
        Serial.println("Error initializing ESP-NOW");
        return;
    }

    esp_now_set_self_role(ESP_NOW_ROLE_COMBO);
    esp_now_register_send_cb(onDataSent);
    esp_now_register_recv_cb(onDataRecv);

    for (int i = 0; i < PLAYER_COUNT; i++)
    {
        if (esp_now_add_peer(addresses[i], ESP_NOW_ROLE_COMBO, 1, NULL, 0) != 0)
        {
            Serial.println("{\"succ\": 0}");
        }
    }
}

void loop()
{
    if (Serial.available() > 0)
    {
        String incomingData = Serial.readStringUntil('\n');

        String player_id = getValueFromJson(incomingData, "player_id");
        String v_str = getValueFromJson(incomingData, "v");
        String w_str = getValueFromJson(incomingData, "w");

        int v = v_str.toInt();
        int w = w_str.toInt();
        int macIndex = getMacAddress(player_id.c_str());

        if (macIndex != -1)
        {
            strncpy(myData.botId, player_id.c_str(), sizeof(myData.botId));
            myData.v = v;
            myData.w = w;
            uint8_t result = esp_now_send(addresses[macIndex], (uint8_t *)&myData, sizeof(myData));

            if (result != 0)
            {
                Serial.println("{\"succ\": 0}");
            }
        }
        else
        {
            Serial.println("{\"succ\": 0}");
        }
    }

    delay(100);
}

String getValueFromJson(String json, String key)
{
    int keyIndex = json.indexOf(key);
    if (keyIndex == -1)
        return "";

    int startIdx = json.indexOf(":", keyIndex) + 1;
    int endIdx = json.indexOf(",", startIdx);
    if (endIdx == -1)
        endIdx = json.indexOf("}", startIdx);

    String value = json.substring(startIdx, endIdx);
    value.trim();
    if (value.startsWith("\"") && value.endsWith("\""))
    {
        value = value.substring(1, value.length() - 1);
    }
    return value;
}

int getMacAddress(const char player_id[32])
{
    for (int i = 0; i < PLAYER_COUNT; i++)
    {
        if (strcmp(playerIds[i], player_id) == 0)
        {
            return i;
        }
    }
    return -1;
}
