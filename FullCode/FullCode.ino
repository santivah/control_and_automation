#include <Wire.h>
//Telegram:
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>
#include <ArduinoJson.h>


#define ADS1115_ADDRESS 0x48

//=================================================================================================================================
// VARIABLE DECLARATIONS 
//=================================================================================================================================

// Telegram part
const char* ssid = "ard-citcea";
const char* password = "ax1ohChooli0quof";

#define BOTtoken "8190157750:AAFva8eCbX0hptrUPS2EWAW8jk-tQ8LceAU"
#define CHAT_ID "7994481953"

WiFiClientSecure client;
UniversalTelegramBot bot(BOTtoken, client);

// Define the pins of the Arduino 
const int SensorPin = A1, RefPin = A2, relayPin = D7;

const int buttonPin = D2;


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

//random number for the part of the code for sending data to python, should delete later 
double number2;

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

bool relayState = LOW;   // Initial state of the relay
unsigned long previous_time = 0; // Stores the last time the pin was toggled


//=================================================================================================================================
// Helper functions: Function created to partition the problem in smaller parts
//=================================================================================================================================
void config_i2c(){
  Wire.begin(); // begin I2C
  // ASD1115
  // set config register and start conversion
  // ANC1 and GND, 4.096v, 128s/

  writeBuf[0] = 1;    // config register is 1
  writeBuf[1] = 0b11010010; // 0xC2 single shot off <== ORIGINAL - single conversion/ AIN1 & GND/ 4.096V/ Continuous (0)
  
  // bit 15 flag bit for single shot
  // Bits 14-12 input selection:
  // 100 ANC0; 101 ANC1; 110 ANC2; 111 ANC3
  // Bits 11-9 Amp gain. Default to 010 here 001 P19
  // Bit 8 Operational mode of the ADS1115.
  // 0 : Continuous conversion mode
  // 1 : Power-down single-shot mode (default)

  writeBuf[2] = 0b11100101; // bits 7-0  0x85 //869 SPS 
  
  // Bits 7-5 data rate default to 100 for 128SPS
  // Bits 4-0  comparator functions see spec sheet.

  // setup ADS1115
  Wire.beginTransmission(ADS1115_ADDRESS);  // ADC 
  Wire.write(writeBuf[0]); 
  Wire.write(writeBuf[1]);
  Wire.write(writeBuf[2]);  
  Wire.endTransmission();  

  delay(500);
}

float read_voltage(){
  //unsigned long start = micros();
  // Read conversion register
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(0x00); // Conversion register
  Wire.endTransmission();

  Wire.requestFrom(ADS1115_ADDRESS, 2);
  int16_t result = Wire.read() << 8 | Wire.read();  // Mount the 2 byte value
  Wire.endTransmission();
  
  //unsigned long end = micros();
  //Serial.print("ADC Read Time (us): ");
  //Serial.println(end - start);

  // Convert result to voltage
  float voltage = result * 4.096 / 32768.0;  // Raw adc * reference voltage configured / maximum adc value
  return voltage;  // Voltage in V
}


//=================================================================================================================================
// setup Function: Function that runs once on startup
//=================================================================================================================================
void setup() {
  Serial.begin(115200);
  config_i2c();
  pinMode(relayPin, OUTPUT);

  pinMode(buttonPin, INPUT); //declare sensor as input

  //Telegram section:
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
  // Read the time in microseconds since the Arduino started
  act_time = micros();
  // Calculate the time difference between the current time and the last time the instantaneous current was updated
  difTime = act_time - time_ant; // in microseconds
  // Serial.print("act_time: ");
  // Serial.println(act_time);
  // Serial.print("time ant: ");
  // Serial.println(time_ant);
  // Serial.print("diftime: ");
  // Serial.println(difTime);
  

  // EVERY 1 MILLISECOND, READ ADC AND CALCULATE THE INSTANTANEOUS CURRENT TO CALCULATE THE RMS
  if (difTime >= 1000) {
    //debug
    //Serial.println("in loop 1");

    // Update the time record with the current time
    time_ant = act_time;

    //=================================================================================================================================
    // Read the voltage from the sensor
    double Vinst = read_voltage() - 1.65;

    // Serial.print("Vinst: ");
    // Serial.println(Vinst);
    //=================================================================================================================================

    //=================================================================================================================================
    // Convert voltage in shunt to current measurement
    double Iinst = Vinst*30; // 30A = 1V
    // Serial.print("Iinst: ");
    // Serial.println(Iinst);
    //=================================================================================================================================
    //=================================================================================================================================
    // Accumulate quadratic sum
    quadratic_sum_rms += Iinst*Iinst*difTime;
    quadratic_sum_v += Vinst*Vinst*difTime;
    //=================================================================================================================================
    quadratic_sum_counter++;

  }

  // EVERY POWER CYCLE (20 ACCUMULATED VALUES), CALCULATE RMS
  if (quadratic_sum_counter >= sampleDuration) {
    //Serial.println("goes in here every power cycle");

    //=================================================================================================================================
    // Take the square root to calculate the RMS of the last power cycle
    double Irms = sqrt(freq*quadratic_sum_rms);
    double Vrms = sqrt(freq*quadratic_sum_v);

    // Serial.print("Vrms: ");
    // Serial.println(Vrms);
    //=================================================================================================================================

    // Reset accumulation values to calculate the RMS of the last power cycle
    quadratic_sum_counter = 0;
    quadratic_sum_rms = 0;
    quadratic_sum_v = 0;

    // Filter base error
    if (Irms<=0.1){
      Irms = 0;
    }
    // Accumulate RMS current values to calculate the average RMS
    accumulated_current += Irms;
    accumulated_counter++;
    
    // Serial.print("Irms: ");
    // Serial.println(Irms);
  }

  // EVERY 250 POWER CYCLES (approximately 5 seconds), CALCULATE THE AVERAGE RMS
  if (accumulated_counter >= sampleAverage) {
    //Serial.println("Goes in here every 250 power cycles");

    //=================================================================================================================================
    // Calculate the average of the RMS current
    double Irms_filt = accumulated_current/((double)accumulated_counter);
    Serial.print("Irms_filt: ");
    Serial.println(Irms_filt);
    // Send a message when the laptop is connected to the electricity
    if (Irms_filt > 400)
      {
        bot.sendMessage(CHAT_ID, "Laptop charging!", "");
      }
    else
      {
        bot.sendMessage(CHAT_ID, "Laptop not charging!", "");
      }
    //=================================================================================================================================

    // Reset accumulation values to calculate the average RMS
    accumulated_current = 0;
    accumulated_counter = 0;

  }


  // toggle the relay on and off 
  if (act_time - previous_time >= 5000000) { // in microseconds. We can change the value to measure the current
    Serial.println("toggles relay");
    previous_time = act_time; // Update the time for the last toggle
    
    // Toggle the relay state
    relayState = !relayState;
    Serial.println(relayState);
    digitalWrite(relayPin, relayState);
  }

  //digitalWrite(relayPin, HIGH); // this means that the switch is off and power does no flow through it 

  // if (digitalRead(buttonPin) == LOW)
  //     {
  //       Serial.println("there is movement");
  //     }
  // else {
  //       Serial.println("there is no movement");
  //     }


}




