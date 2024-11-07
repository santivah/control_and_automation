int number1 = 42; // First number to print
pychaint number2 = 17; // Second number to print

void setup() {
  Serial.begin(9600); // Initialize serial communication at 9600 baud
}

void loop() {
  // Print the two numbers
  Serial.print(number1);
  Serial.print(";");
  Serial.print(number2);
  Serial.println(";");
  number1++;
  number2++;

  delay(2000); // Wait for 2000 milliseconds (2 seconds) before the next print
}