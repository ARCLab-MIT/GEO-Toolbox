from datetime import datetime, timezone
from histories import history

def get_timestamp(date:str): # convert date to datetime
    return datetime.fromisoformat(date + " 00:00:00+00:00").astimezone(timezone.utc)

# INPUTS
satcat = 27632 # satellite norad ID
start_date = get_timestamp("2016-08-01") # date of first ephemeride
end_date = get_timestamp("2021-10-01") # date of last ephemeride

# INITIALIZE SATELLITE HISTORY
NIMIQ2 = history(satcat,start_date,end_date)

# RETRIEVE HISTORIAL GEOGRAPHIC COORDINATES
datetimes, longitudes, latitudes, altitudes = NIMIQ2.LLA() # degrees (-180 to 180) & meters
datetimes, clean_longitudes, clean_latitudes, altitudes = NIMIQ2.CleanLLA() # degrees (continuous) & meters

# RETRIEVE HISTORICAL ORBITAL ELEMENTS
datetimes, ecc, a, inclination, raan, argp, nu, fa = NIMIQ2.OE()

# PLOT LONGITUDE SEGMENT
t1 = get_timestamp("2019-05-20")
t2 = get_timestamp("2019-09-20")
NIMIQ2.PlotEpochColors(datetimes,clean_longitudes,t1=t1,t2=t2,title="Longitude")

print("FIN demo.py")