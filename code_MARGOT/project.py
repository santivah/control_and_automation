import requests
import datetime
import time
import wmi
import ctypes
from ctypes import wintypes
import serial
import re
import pandas as pd

######################################
# CONFIGURATION CONSTANTS
######################################
CARBON_INTENSITY_API_URL = 'https://api.electricitymap.org/v3/carbon-intensity/latest'
CARBON_INTENSITY_TOKEN = 'ATSASQPg3AZYu'
CARBON_INTENSITY_THRESHOLD = 90  # gCO2eq/kWh threshold for eco-friendly charging
DEFAULT_PORT = "COM3"
BAUD_RATE = 9600
FULL_CHARGE_CAPACITY = 37.979  # in mWh
VOLTAGE = 11.1 #V

######################################
# API UTILITIES
######################################

def get_carbon_intensity(zone="ES"):
    """
    Fetch the latest carbon intensity for the specified zone.
    :param zone: Zone code for the API request (e.g., "ES" for Spain).
    :return: Carbon intensity (gCO2eq/kWh) and timestamp as a tuple.
    """

    headers = {'auth-token': CARBON_INTENSITY_TOKEN}
    params = {'zone': zone}
    response = requests.get(CARBON_INTENSITY_API_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    carbon_intensity = data['carbonIntensity']
    timestamp = datetime.datetime.strptime(data['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z")
    return carbon_intensity, timestamp

######################################
# SERIAL COMMUNICATION
######################################

def initialize_serial_connection(port=DEFAULT_PORT, baud_rate=BAUD_RATE, timeout=1):
    """
    Initialize the serial connection with the Arduino.
    """
    try:
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        time.sleep(2)  # Allow Arduino to initialize
        return ser
    except serial.SerialException as e:
        print(f"Error initializing serial connection: {e}")
        return None

def measure_current(serial_conn):
    """
    Take a single currentmeasurement from the Arduino via serial connection.
    :param serial_conn: Initialized serial connection.
    :return: Measured current in amperes or None if no data received.
    """
    try:
        if serial_conn and serial_conn.in_waiting > 0:
            line = serial_conn.readline().decode('utf-8').strip()
            current_match = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)
            if current_match:
                return float(current_match[0])
        return None
    except Exception as e:
        print(f"Error reading current measurement: {e}")
        return None

def relay_on(serial_conn):
    """
    Send command to turn the relay on.
    """
    if serial_conn:
        serial_conn.write(b'ON\n')
        print("Sent: ON")

def relay_off(serial_conn):
    """
    Send command to turn the relay off.
    """
    if serial_conn:
        serial_conn.write(b'OFF\n')
        print("Sent: OFF")

######################################
# BATTERY MANAGEMENT
######################################
def get_battery_state():
     """
     Returns the battery state: 1 = Not charging, 2 = Charging.
     """
     c = wmi.WMI()
     batteries = c.Win32_Battery()
     #print(batteries[0].BatteryStatus)
     
     return batteries[0].BatteryStatus

def get_battery_percentage():
    """
    Returns the estimated charge percentage of the battery.
    """
    c = wmi.WMI()
    batteries = c.Win32_Battery()
    #print(batteries[0].EstimatedChargeRemaining)
    return batteries[0].EstimatedChargeRemaining

# def calculate_remaining_time(full_charge_capacity, current_capacity, charging_current, VOLTAGE):
#     """
#     Calculates remaining charging time.
#     :param full_charge_capacity: Total battery capacity in mWh.
#     :param current_capacity: Current battery charge in mWh.
#     :param charging_current: Current used for charging in mA.
#     :param voltage: Nominal voltage of the battery (V)
#     :return: Remaining time in minutes.
#     """
    
#     remaining_capacity = (full_charge_capacity - current_capacity)*1000
#     return (remaining_capacity / (charging_current * VOLTAGE)) * 60  # Convert hours to minutes

def calculate_remaining_charge_time():
    # charge for 5 minutes 
    relay_off(serial_conn)
    
    # see charge percentage 
    initial_charge = get_battery_percentage()
    
    # wait for 5 minutes to get charging rate 
    print("Waiting for 5 minutes to gather charging data...")
    time.sleep(300)  
    
    new_charge = get_battery_percentage()
    
    # Calculate the charging rate (percentage per minute)
    charge_rate = (new_charge - initial_charge) / 5  # Since 5 minutes have passed
    print(f"Charging Rate: {charge_rate} % per minute")
    
    # Calculate time to full charge
    time_to_full_charge = (100 - new_charge) / charge_rate  # in minutes
    print(f"Estimated Time to Full Charge: {time_to_full_charge} minutes")

    return time_to_full_charge

######################################
# CHARGING WINDOW MANAGEMENT
######################################

def get_user_time_input(prompt_text):
    """
    Ask the user for a time in 'HH:MM' format and return a datetime.time object.
    """
    while True:
        try:
            time_str = input(f"{prompt_text} (HH:MM): ")
            hours, minutes = map(int, time_str.split(":"))
            return datetime.time(hours, minutes)
        except ValueError:
            print("Invalid format. Please use HH:MM (e.g., 22:00).")

def get_charging_window():
    """
    Get the desired charging window from the user.
    """
    start_time = get_user_time_input("Enter start charge time")
    end_time = get_user_time_input("Enter end charge time")
    today = datetime.date.today()
    start_dt = datetime.datetime.combine(today, start_time)
    end_dt = datetime.datetime.combine(today, end_time)
    if end_dt <= start_dt:
        end_dt += datetime.timedelta(days=1)
    print(f"Charging window: {start_dt} --> {end_dt}")
    return start_dt, end_dt

######################################
# CONTROL CHARGING
######################################

def control_charging(start_dt, end_dt, serial_conn):
    """
    Control the charging process based on the user-defined window and battery state.
    """
    while True:
        now = datetime.datetime.now()

        if now >= end_dt:
            print("End of charging window reached. Stopping control loop.")
            relay_on(serial_conn)
            break

        if now < start_dt:
            print(f"Waiting for start time... (now={now}, start={start_dt})")
            time.sleep(60)
            continue

        percentage = get_battery_percentage()
        # current_capacity = FULL_CHARGE_CAPACITY * (percentage / 100)
        # estimated_time = calculate_remaining_time(FULL_CHARGE_CAPACITY, current_capacity, charging_current, VOLTAGE)
        estimated_time = calculate_remaining_charge_time()
        time_left_in_window = (end_dt - now).total_seconds() / 60.0
        carbon_intensity, _ = get_carbon_intensity()
        print(f"Time left in window: {time_left_in_window:.1f} min")
        print(f"Battery needs: {estimated_time:.1f} min to be full.")
        print(f"Current carbon intensity: {carbon_intensity} gCO2eq/kWh.")

        if estimated_time <= 0.1:
            print("The computer is fully charged.")
            relay_on(serial_conn)
            break

        if time_left_in_window <= estimated_time:
            print("Charging relay OFF (must reach 100% by deadline).")
            relay_off(serial_conn)
        elif carbon_intensity  <= CARBON_INTENSITY_THRESHOLD:
            print("Charging relay OFF (carbon emissions are low).")
            relay_off(serial_conn)
        else:
            print("Charging relay ON (carbon emissions are high).")
            relay_on(serial_conn)

        time.sleep(60)

######################################
# MAIN EXECUTION
######################################

if __name__ == "__main__":
    # Initialize serial connection
    serial_conn = initialize_serial_connection()

    # Get the charging window
    start_dt, end_dt = get_charging_window()

    status = get_battery_state()
    charging_current = measure_current(serial_conn)

    relay_off(serial_conn)
    time.sleep(2)

    if charging_current is None:
        print("Computer is not charging.")
    elif status == 1:
        print("Computer is not plugged in.")
    else:
        # Start the control loop
        if serial_conn:
            control_charging(start_dt, end_dt, serial_conn)
            serial_conn.close()
