const int buttonPin = 2; // Use digital pin 2 for the button
int previousState = LOW; // Store the last state (LOW or HIGH)

void setup() {
  // Initialize Serial communication
  Serial.begin(115200); 

  // Set the button pin as input
  pinMode(buttonPin, INPUT); // INPUT assumes an external pull-up/pull-down resistor
}

void loop() {
  int currentState = digitalRead(buttonPin);
  Serial.println(currentState);
  if (currentState != previousState) {
    if (currentState == HIGH) {
      Serial.println("Object detected within range!");
    } else {
      Serial.println("Object moved out of range!");
    }
    previousState = currentState;
  }
}


  //if (digitalRead(buttonPin) == LOW) {
    //Serial.println("there is movement");
  //} else {
    //Serial.println("there is no movement");
  //}
//}