#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>
#include <ArduinoJson.h>

const char* ssid = "ard-citcea";
const char* password = "ax1ohChooli0quof";

#define BOTtoken "8190157750:AAFva8eCbX0hptrUPS2EWAW8jk-tQ8LceAU"
#define CHAT_ID "7994481953"

WiFiClientSecure client;
UniversalTelegramBot bot(BOTtoken, client);

void setup() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  client.setCACert(TELEGRAM_CERTIFICATE_ROOT);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  bot.sendMessage(CHAT_ID, "hi", "");
}

void loop() {
  //bot.sendMessage(CHAT_ID, "Attention!");

}
