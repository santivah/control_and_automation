
"""

"""

import psutil
this = psutil.sensors_battery()
# sbattery(percent=0.0, secsleft=-1, power_plugged=None)
that = psutil.sensors_battery().power_plugged
# None
print(this)