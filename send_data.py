import serial
import time

# Set up the serial connection (change COM3 to your correct port)
ser = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)  # Wait for the Arduino to initialize

try:
    while True:
        # Send 'ON' to Arduino to turn the LED on
        ser.write(b'ON\n')
        print("Sent: ON")
        time.sleep(2)  # Wait for 2 seconds

        # Send 'OFF' to Arduino to turn the LED off
        ser.write(b'OFF\n')
        print("Sent: OFF")
        time.sleep(2)  # Wait for 2 seconds

except KeyboardInterrupt:
    print("Program interrupted by user.")
finally:
    ser.close()  # Close the serial connection
