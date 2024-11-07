
# python file from Nov 7 by heather


import serial
import time
import re


# set up serial port
ser = serial.Serial('COM3', 9600, timeout =1)
time.sleep(2)