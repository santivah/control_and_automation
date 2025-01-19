// help code for python

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>
#include <ArduinoJson.h>
#include <Wire.h>

#define ADS1115_ADDRESS 0x48
#define BOTtoken "8190157750:AAFva8eCbX0hptrUPS2EWAW8jk-tQ8LceAU" // for telegram bot 
#define CHAT_ID "7994481953" // for telegram bot 

// Define the pins of the Arduino 
const int SensorPin = A1, RefPin = A2, relayPin = D7;
const int UltrasonicPin = 2; // Digital Pin 2 is for the ultrasonic sensor 

// Define the data from the current sensor
const int Rshunt = 33.3;                // Resistance of the transformer: Model 50 A: 20 ohms, Model 30 A: 33.3 ohms
double n_trafo = 1000;                  // Number of turns between primary and secondary

// Variables to calculate every millisecond
unsigned long time_now = 0;
unsigned long time_ant = 0, difTime = 0, act_time = 0, reading_time = 0, dif_reading_time = 0, timer1 = 0, timer2 = 0;
 
// Define variables to calculate the RMS of a power cycle
double quadratic_sum_v = 0.0;
double quadratic_sum_rms = 0.0;   // This variable accumulates the quadratic sum of instantaneous currents
const int sampleDuration = 20;    // Number of samples that determine how often the RMS is calculated
int quadratic_sum_counter = 0;    // Counter of how many times values have been accumulated in the quadratic sum
double freq = 50.0;               // Define the frequency of the power cycle

// Define variables to calculate an average of the current
double accumulated_current = 0.0;       // Accumulator of RMS values for averaging
const int sampleAverage = 250;          // Number of samples that determine how often the RMS average is calculated
int accumulated_counter = 0;            // Counter of how many times RMS values have been accumulated
bool first_run = true;
double v_calib_acum = 0;
double v_calib = 0;
int i = 0;
byte writeBuf[3];

double Irms_filt = 0;

// Define variables for the telegram bot 
const char* ssid = "ard-citcea";
const char* password = "ax1ohChooli0quof";

WiFiClientSecure client;
UniversalTelegramBot bot(BOTtoken, client);

//=================================================================================================================================
// Helper functions: Function created to partition the problem in smaller parts
//=================================================================================================================================
void config_i2c(){
  Wire.begin(); // begin I2C
  // ADS1115 configuration
  writeBuf[0] = 1;    // config register is 1
  writeBuf[1] = 0b11010010; // single conversion, AIN1 & GND, 4.096V, Continuous
  writeBuf[2] = 0b11100101; // 869 SPS

  Wire.beginTransmission(ADS1115_ADDRESS);  // ADC 
  Wire.write(writeBuf[0]); 
  Wire.write(writeBuf[1]);
  Wire.write(writeBuf[2]);  
  Wire.endTransmission();  
  delay(500);
}

float read_voltage(){
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(0x00); // Conversion register
  Wire.endTransmission();

  Wire.requestFrom(ADS1115_ADDRESS, 2);
  int16_t result = Wire.read() << 8 | Wire.read();  // Mount the 2 byte value
  Wire.endTransmission();

  float voltage = result * 4.096 / 32768.0;  // Raw adc * reference voltage configured / maximum adc value
  return voltage;  // Voltage in V
}

//=================================================================================================================================
// setup Function: Function that runs once on startup
//=================================================================================================================================
void setup() {
  Serial.begin(9600);
  config_i2c();
  pinMode(SensorPin, INPUT); // declare sensor as input
  pinMode(relayPin, OUTPUT);
  pinMode(UltrasonicPin, INPUT); // ultrasonic sensor pin is input 

  // for telegram:
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  client.setCACert(TELEGRAM_CERTIFICATE_ROOT);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

}

//=================================================================================================================================
// loop Function: Function that runs cyclically indefinitely
//=================================================================================================================================
void loop() {

  // Check for serial input
  if (Serial.available() > 0) {
      String command = Serial.readStringUntil('\n');  // Read until newline

      if (command == "ON") {
          digitalWrite(relayPin, HIGH);  // Turn the relay on
          Serial.println("Relay ON");
      } else if (command == "OFF") {
          digitalWrite(relayPin, LOW);   // Turn the relay off
          Serial.println("Relay OFF");
      } else if (command.startsWith("MSG:")) {  // Check if the command is a Telegram message
          String message = command.substring(4);  // Extract the message after "MSG:"
          bot.sendMessage(CHAT_ID, message, "");
      }
  }

  // Read the time in microseconds since the Arduino started
  act_time = micros();
  // Calculate the time difference between the current time and the last time the instantaneous current was updated
  difTime = act_time - time_ant; // in microseconds

  // EVERY 1 MILLISECOND, READ ADC AND CALCULATE THE INSTANTANEOUS CURRENT TO CALCULATE THE RMS
  if (difTime >= 1000) {
    // Update the time record with the current time
    time_ant = act_time;

    // Read the voltage from the sensor
    double Vinst = read_voltage() - 1.65;

    // Convert voltage in shunt to current measurement
    double Iinst = Vinst * 30; // 30A = 1V

    // Accumulate quadratic sum
    quadratic_sum_rms += Iinst * Iinst * difTime;
    quadratic_sum_v += Vinst * Vinst * difTime;
    quadratic_sum_counter++;
  }

  // EVERY POWER CYCLE (20 ACCUMULATED VALUES), CALCULATE RMS
  if (quadratic_sum_counter >= sampleDuration) {
    // Take the square root to calculate the RMS of the last power cycle
    double Irms = sqrt(freq * quadratic_sum_rms);
    double Vrms = sqrt(freq * quadratic_sum_v);

    // Reset accumulation values to calculate the RMS of the last power cycle
    quadratic_sum_counter = 0;
    quadratic_sum_rms = 0;
    quadratic_sum_v = 0;

    // Filter base error
    if (Irms <= 0.1) {
      Irms = 0;
    }
    // Accumulate RMS current values to calculate the average RMS
    accumulated_current += Irms;
    accumulated_counter++;
  }

  // EVERY 250 POWER CYCLES (approximately 5 seconds), CALCULATE THE AVERAGE RMS and print the Ultrasonic sensor reading 
  if (accumulated_counter >= sampleAverage) {
    // Calculate the average of the RMS current
    double Irms_filt = accumulated_current / ((double)accumulated_counter);
    Serial.print("Irms_filt: ");
    Serial.println(Irms_filt);

    // Reset accumulation values to calculate the average RMS
    accumulated_current = 0;
    accumulated_counter = 0;

    Ultrasonic = digitalRead(UltrasonicPin) // LOW corresponds to object nearby 
    Serial.print("Ultrasonic: ");
    Serial.println(Ultrasonic);

  }
}