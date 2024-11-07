
# python file from Nov 7 by heather


import serial
import time
import re
import pandas as pd
from datetime import datetime

# set up serial connection (adjust 'COM3' to your correct part)
ser = serial.Serial('COM3', 9600, timeout =1)
time.sleep(2) # wait for Arduino to initialize
df.pd.DataFram(columns=["Datetime",])

