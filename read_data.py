import serial
import time
import re
import pandas as pd
from datetime import datetime

# Set up the serial connection (adjust 'COM3' to your correct port)
ser = serial.Serial('COM3', 9600, timeout=1)  # Change COM3 to your port
time.sleep(2)  # Wait for the Arduino to initialize

# initialize dataframe
df = pd.DataFrame(columns=["Datetime", "v1", "v2"])

try:
    while True:
        # Check if data is available to read
        if ser.in_waiting > 0:
            # Read a line from the serial port, decode it and remove newline characters
            line = ser.readline().decode('utf-8').strip()

            # Get the current timestamp
            timestamp = datetime.now()

            v1, v2 = re.findall(pattern=r"[-+]?\d*\.\d+|[-+]?\d+", string=line)
            print("v1: ", v1, "v2: ", v2)
            # Print the received data from Arduino

            # Append the data to the DataFrame
            new_row = {"Datetime": timestamp, "v1": v1, "v2": v2}
            df = df.append(new_row, ignore_index=True)
except KeyboardInterrupt:
    # Handle manual interruption (e.g., pressing Ctrl+C)
    print("Program interrupted by user.")
finally:
    # Close the serial port when the program ends
    ser.close()

    # Save the DataFrame to a CSV file
    df.to_csv("sensor_data.csv", index=False)

