import requests
import datetime
import time
import wmi
import ctypes
from ctypes import wintypes

######################################
# CO2 intensity API
######################################

# CHECK ZONES
my_token = 'ATSASQPg3AZYu'
base_prod_url = "https://api.electricitymap.org/v3/zones"

response = requests.get(base_prod_url)

data_dict = response.json()

for abbreviation, country_info in data_dict.items():
    country_name = country_info["zoneName"] # ES is for Spain

# CO2 INTESNITY API
url = 'https://api.electricitymap.org/v3/carbon-intensity/latest'
headers = {'auth-token': 'ATSASQPg3AZYu'}
params = {'zone': 'ES'}

response = requests.get(url, headers=headers, params=params)

data_json = response.json()
#print(data_json)

carbonIntensity = data_json['carbonIntensity']
current_time =  datetime.datetime.strptime(data_json['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z")

######################################
# STATE OF BATTERY
######################################
def get_battery_state():
    """
    Returns the battery state.
    Common values:
      1 = Not charging
      2 = Charging
    """
    c = wmi.WMI()
    batteries = c.Win32_Battery()
    return batteries[0].BatteryStatus

######################################
# PERCENTAGE OF BATTERY
######################################
def get_battery_percentage():
    c = wmi.WMI()
    batteries = c.Win32_Battery()
    return batteries[0].EstimatedChargeRemaining

######################################
# GET REMAINING CHARGING TIME
######################################
def get_remaining_charging_time():
    """
    Returns the remaining battery time (in minutes) from WMI on Windows.
    """
    state = get_battery_state()
    if state == 2:  # 2 = Charging
        c = wmi.WMI()
        batteries = c.Win32_Battery()
        if batteries[0].EstimatedRunTime == 71582788: # code is not supported
            print("Code is not supported")
            return None
        else:
            return batteries[0].EstimatedRunTime  # in minutes
    # If battery is discharging or fully charged, we return None.
    print("Computer is not charging")
    return None

######################################
# CHARGING WINDOW
######################################
# Function to ask desired start/end time
def get_user_time_input(prompt_text):
    """
    Ask the user for a time in 'HH:MM' format,
    and return a datetime.time object.
    """
    while True:
        time_str = input(prompt_text + " (HH:MM): ")
        try:
            hours, minutes = map(int, time_str.split(":"))
            return datetime.time(hours, minutes)
        except ValueError:
            print("Invalid format. Please use HH:MM (e.g. 22:00).")

start_time_input = get_user_time_input("Enter start charge time")
end_time_input = get_user_time_input("Enter end charge time")

# For simplicity, assume 'today' for start_time and 'today' or 'tomorrow' for end_time
today = datetime.date.today()

start_dt = datetime.datetime.combine(today, start_time_input)

# If the end time is logically "before" the start (e.g. user sets 07:00 next day),
# we assume it’s the next day:
end_dt = datetime.datetime.combine(today, end_time_input)
if end_dt <= start_dt:
    # end time is next day
    end_dt += datetime.timedelta(days=1)

print(f"Charging window: {start_dt} --> {end_dt}")

######################################
# CONTROL LOOP
######################################
def control_charging(start_dt, end_dt):
    while True:
        now = datetime.datetime.now()

        if now >= end_dt:
            print("End of charging window reached. Stopping control loop.")
            # Ensure relay OFF
            break

        if now < start_dt:
            # Too early to start charging.
            print(f"Waiting to reach start time... (now={now}, start={start_dt})")
            # Relay OFF
            continue

        time_left_in_window = (end_dt - now).total_seconds() / 60.0
        # estimated_charge_time = 50
        estimated_charge_time = get_remaining_charging_time()

        if estimated_charge_time is None:
            break
        else:
            print(f"Time left in window: {time_left_in_window:.1f} min, "
            f"Battery needs: {estimated_charge_time:.1f} min to be full")

        if time_left_in_window <= estimated_charge_time:
            # We must charge now (or continue charging) to ensure 100% by end_dt
            print("Charging relay ON (must reach 100% by deadline).")
            # ... code to switch relay ON ...
        else:
            if carbonIntensity <= 90:  # threshold is 130g CO2 eq/ kWh
                print("Charging relay ON (carbon emission is low)")
                # ... code to switch relay ON ...
            else:
                print("Charging relay OFF (carbon emission is high)")
                # ... code to switch relay OFF ...
        time.sleep(60)

# Run the control loop
control_charging(start_dt, end_dt)