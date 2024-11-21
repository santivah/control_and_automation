
// constants won't change. Used here to set a pin number:
const int relayPin = D7;  

void setup() {
  Serial.begin(115200);
  pinMode(relayPin, OUTPUT);
}

void loop() {

  // sending signals to the relay 
  digitalWrite(relayPin, HIGH);
  delay(2000);

  digitalWrite(relayPin, LOW);
  delay(2000);

}
