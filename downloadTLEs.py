import spacetrack.operators as op
from spacetrack import SpaceTrackClient
import datetime as dt
import numpy as np
from time import sleep
import csv
from pathlib import Path

# Check whether ./Data/TLEs/ exists. If not, make it.
path = '../Data/TLEs/'
Path(path).mkdir(parents=True, exist_ok=True)

# Prompt user for Space-Track log-in credentials
print("Log in to using your Space-Track.org account credentials.\n")
st_email = input("Email: ")
st_pass = input("Password: ")

# Log in to Space-Track using your email and password
st = SpaceTrackClient(identity=st_email, password=st_pass)

# Make a list of all the satcats in Data/trimmedsatcats.csv
satcats = []
with open("../Data/satcats.csv", encoding='utf-8-sig') as f:
	reader = csv.reader(f, delimiter=",")
	for row in reader:
		satcats.append(row[0])

print("Define a study period (using yyyy-mm-dd formats).\n")
studyperiod_start = input("Start date: ")
studyperiod_end = input("End date: ")

# Only pull TLEs from between the start date and the end date
drange = op.inclusive_range(dt.datetime(int(studyperiod_start[0:4]), int(studyperiod_start[5:7]), int(studyperiod_start[8:10])), dt.datetime(int(studyperiod_end[0:4]), int(studyperiod_end[5:7]), int(studyperiod_end[8:10])))

# Download the TLEs and save them in Data/TLEs/[satcat].txt
for satcat in satcats: 
    with open('../Data/TLEs/'+str(satcat)+'.txt','w') as f: 
        f.write(st.tle(norad_cat_id=satcat, epoch=drange, orderby='epoch desc', format='tle'))
        f.close()
    print("Printed file: " + str(satcat) + ".txt.")
    for i in range(26):
    	if i < 13:
    		print("*"*(i+1))
    		sleep(0.5)
    	else:
    		print("*"*(26-i))
    		sleep(0.5)