int ledPin = 13;  // Pin where the LED is connected

void setup() {
  // Initialize the serial communication
  Serial.begin(9600);
  
  // Set the LED pin as an output
  pinMode(ledPin, OUTPUT);
}

void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    // Read the incoming byte (either 'ON' or 'OFF')
    String command = Serial.readStringUntil('\n');  // Read until newline

    // Check if the command is 'ON'
    if (command == "ON") {
      digitalWrite(ledPin, HIGH);  // Turn the LED on
    }
    // Check if the command is 'OFF'
    else if (command == "OFF") {
      digitalWrite(ledPin, LOW);   // Turn the LED off
    }
  }
}