from datetime import datetime, timezone, timedelta
from search_parameters import *
import numpy as np

def expand(longitude):
    exlon = np.array(longitude)
    for i in range(1,len(longitude)):
        l0 = exlon[i-1]
        l1 = exlon[i]
        ld = l0 - l1
        if np.abs(exlon[i-1]-exlon[i])>180:
            s = -1 if ld < 0 else 1
            n = 180 if np.abs(l1) <= 180 else 360
            exlon[i] = l1 + (n*(int(ld/n)+s))
    return exlon

def contract(exlon):
    lon360 = exlon - int(exlon/360)*360 if exlon >= 0 else 360 + exlon - int(exlon/360)*360
    lon180 = lon360 if lon360 <=180 else -1*(360-lon360)
    return {'360':lon360, '180':lon180}

##############################################################################
'''Helper Functions and Variables for Improved Readability'''

# visual divider for print statements
div = "__"*25

# easy datetime conversion
def timestamp(date):
    '''
    Formats a date string into an offset-aware datetime object. Datetime objects must be offset-aware for
    comparison with most astrometric timestamp formats.
    %Y = year, %m = month, %d = day, %H = hour, %M = minute, %S = second, %f = microsecond, %z = timezone
    More info: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    '''
    if type(date) == datetime: 
        # check if date is offset aware
        if date.tzinfo is None: return date.replace(tzinfo=timezone.utc)
        else: return date
    else: return datetime.strptime(date+" 00:00:00.000000+0000",'%Y-%m-%d %H:%M:%S.%f%z')

# colorblind friendly palette
GREEN = "#337538" 
BLUE = "#94caec"
RED = "#c26a77"
PURPLE = "#9f4a97"

# debug helpers
def export_saterrors(sat_errors):
    with open(data_directories.home+"sat_errors.txt","w") as f:
        for sat in sat_errors:
            f.write(sat+"\n")
def debug_print(txt):
    if debug: print(txt)
def safedex(dex,flag=False):
    newdex = dex if dex is not None else 0
    if flag:
        if dex is None: return newdex, False
        else: return dex, True
    else: return newdex
##############################################################################