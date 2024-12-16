const int buttonPin = 2; // Use digital pin 2 for the button

void setup() {
  // Initialize Serial communication
  Serial.begin(115200); 

  // Set the button pin as input
  pinMode(buttonPin, INPUT); // INPUT assumes an external pull-up/pull-down resistor
}

void loop() {
  // Read the button state
  if (digitalRead(buttonPin) == LOW) {
    Serial.println("there is movement");
  } else {
    Serial.println("there is no movement");
  }
}