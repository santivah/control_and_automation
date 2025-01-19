#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>
#include <ArduinoJson.h>

const char* ssid = "Livebox6-D583";
const char* password = "5c9s73JvCLSP";

#define BOTtoken "8155772892:AAE2sAqJJvUCjtoRNNvujKla7bq-woFEDzI"
#define CHAT_ID "7610829513"

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
