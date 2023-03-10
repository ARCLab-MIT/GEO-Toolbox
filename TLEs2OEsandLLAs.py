import numpy as np
import ephem
import datetime
import csv
import signal
import matplotlib.dates
import matplotlib.pyplot as plt
from dms2decimal import dms
from pathlib import Path

# Check whether ./Data/TLEs/ exists. If not, make it.
path = '../Data/OEs and LLAs/'
Path(path).mkdir(parents=True, exist_ok=True)

# Write out an exception for calculations that take too long
class TimeoutException(Exception):   # Custom exception class
    pass
def timeout_handler(signum, frame):   # Custom signal handler
    raise TimeoutException
signal.signal(signal.SIGALRM, timeout_handler) # Change the behavior of SIGALRM

# Create a list of satellite ID numbers from the Data/satcats.csv file
satcats = []
with open("../Data/satcats.csv", encoding='utf-8-sig') as f:
	reader = csv.reader(f, delimiter=",")
	for row in reader:
		satcats.append(row[0])

# Write a quick function that finds the number of rows in a text file
def file_len(fname):
    with open(fname) as f:
    	lines = len(f.readlines())
    return lines

# Write a function that helps find the nearest epoch available for a given date
def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

# Define some Earth-specific parameters for some future calculations
G = 6.67408 * 10**-11 # Gravitational constant in m^3 kg^-1 s%-2
M = 5.972 * 10**24 # Mass of the Earth in kg
Re = 6.371 * 10**6 # Radius of the Earth in m
A = 42164.2 * 10**3 # Unperturbed geostationary semimajor axis in m

# Prompt the user to choose a study period
print("Define a study period (using yyyy-mm-dd formats).\n")
studyperiod_start = input("Start date: ")
studyperiod_end = input("End date: ")

# studyperiod_start = "2021-11-01"
# studyperiod_end = "2021-12-31"

# Prompt the user to choose a time step
print("Choose a time step (in days).\n")
timestep = input("Time step: ")

# timestep = 0.5

# Create a list of dates between the start date and the end date
startdate = matplotlib.dates.date2num(datetime.datetime(int(studyperiod_start[0:4]), int(studyperiod_start[5:7]), int(studyperiod_start[8:10]), 0, 0, 0))
enddate = matplotlib.dates.date2num(datetime.datetime(int(studyperiod_end[0:4]), int(studyperiod_end[5:7]), int(studyperiod_end[8:10]),0, 0, 0))
timesteps = np.arange(int(startdate), int(enddate)+float(timestep), float(timestep))

# For each satellite in Data/satcats.csv, find the date of the first epoch (which appears last in the TLE file)
firstepochs = []
for satcat in satcats:
	index = []
	for a in np.arange(0,file_len('../Data/TLEs/'+str(satcat)+'.txt'),2):
		index.append(a)
	with open('../Data/TLEs/'+str(satcat)+'.txt') as h: 
		lines = h.readlines()
		name = str(satcat);
		line1 = str(lines[index[-1]].strip());
		line2 = str(lines[index[-1]+1].strip());
		year_snippet = line1[18:20]
		if int(year_snippet)<57:
			year = int("20"+year_snippet)
		else:
			year = int("19"+year_snippet)
		day_snippet = line1[20:32]
		fulldate = datetime.datetime(year,1,1,0,0,0)+datetime.timedelta(days=float(day_snippet))
		matplotlib_datetime = matplotlib.dates.date2num(fulldate)
		# Compute the TLEs orbital paramters at time of its epoch
		firstepochs.append(matplotlib_datetime)

# For each satellite in Data/geosatcats.csv, find the date of the last epoch (which appears first in the TLE file)
lastepochs = []
for satcat in satcats:
	with open('../Data/TLEs/'+str(satcat)+'.txt') as h: 
		lines = h.readlines()
		name = str(satcat);
		line1 = str(lines[0].strip());
		year_snippet = line1[18:20]
		if int(year_snippet)<57:
			year = int("20"+year_snippet)
		else:
			year = int("19"+year_snippet)
		day_snippet = line1[20:32]
		fulldate = datetime.datetime(year,1,1,0,0,0)+datetime.timedelta(days=float(day_snippet))
		matplotlib_datetime = matplotlib.dates.date2num(fulldate)
		# Compute the TLEs orbital paramters at time of its epoch
		lastepochs.append(matplotlib_datetime)

# For each satellite, make a new csv file with orbital elements (OEs) and geographic coordinates (LLAs)
for satcat, firstepoch, lastepoch in zip(satcats,firstepochs, lastepochs):
	# Make a csv file to house the LLA data
	with open('../Data/OEs and LLAs/'+str(satcat)+'.csv', 'w') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["Time step", "TLE epoch", "Eccentricity", "Semimajor axis (m)", "Inclination (deg)", "RAAN (deg)", "Argument of periapsis (deg)", "Mean anomaly (deg)", "True anomaly (deg)", "Latitude (deg)", "Longitude (deg)", "Altitude (m)"])
	# Start by making a list of all the epochs included in the TLE file for each satellite
	list_of_datetimes = []
	index = []
	for a in np.arange(0, file_len('../Data/TLEs/'+str(satcat)+'.txt'), 2):
		index.append(a)
	with open('../Data/TLEs/'+str(satcat)+'.txt') as h: 
		lines = h.readlines()
		for x in index:
			name = str(satcat);
			line1 = str(lines[x].strip());
			line2 = str(lines[x+1].strip());
			year_snippet = line1[18:20]
			if int(year_snippet)<57:
				year = int("20"+year_snippet)
			else:
				year = int("19"+year_snippet)
			day_snippet = line1[20:32]
			fulldate = datetime.datetime(year,1,1,0,0,0)+datetime.timedelta(days=float(day_snippet))
			list_of_datetimes.append(fulldate)
	matplotlib_datetimes = matplotlib.dates.date2num(list_of_datetimes)
	for t in timesteps:
		# Find the nearest epoch to each timestep
		nearest_time = nearest(matplotlib_datetimes, t)
		# Don't compute any date for days before the satellite's first public epoch
		if (abs(t - nearest_time) < 14 and t > firstepoch - 14 and t < lastepoch + 14):
			index = []
			for a in np.arange(0,file_len('../Data/TLEs/'+str(satcat)+'.txt'),2):
				index.append(a)
			with open('../Data/TLEs/'+str(satcat)+'.txt') as g: 
				lines = g.readlines()
				for x in index:
					name = str(satcat);
					line1 = str(lines[x].strip());
					line2 = str(lines[x+1].strip());
					year_snippet = line1[18:20]
					if int(year_snippet)<57:
						year = int("20"+year_snippet)
					else:
						year = int("19"+year_snippet)
					day_snippet = line1[20:32]
					fulldate = datetime.datetime(year,1,1,0,0,0)+datetime.timedelta(days=float(day_snippet))
					date = matplotlib.dates.date2num(fulldate)
					if date == nearest_time: 
						try:
							tle_rec = ephem.readtle(name, line1, line2)
							tle_rec.compute(matplotlib.dates.num2date(t))
							# Pull or derive all of the classical OEs
							meanmotion = tle_rec._n * 2 * np.pi / 86400 # rad/s
							eccentricity = tle_rec._e # unitless
							semimajor = np.cbrt((G * M)/(meanmotion**2)) # in m
							apogee = semimajor * (1 + tle_rec._e) - Re # in m
							perigee = semimajor * (1 - tle_rec._e) - Re # in m
							inclination = dms(str(tle_rec._inc)) # in decimal degrees
							RAAN = dms(str(tle_rec._raan)) # in decimal degrees
							argperi = dms(str(tle_rec._ap)) # in decimal degrees
							meananomaly = dms(str(tle_rec._M)) # in decimal degrees
							trueanomaly = meananomaly + (2*eccentricity - 0.25*eccentricity**3)*np.sin(meananomaly) + 1.25*eccentricity**2*np.sin(2*meananomaly)+(13/12)*eccentricity**3*np.sin(3*meananomaly)
							longitude = dms(str(tle_rec.sublong))
							latitude = dms(str(tle_rec.sublat))
							# To solve for the altitude, calculate the range between each satellite and its subsatellite point
							subsatellitepoint = ephem.Observer()
							subsatellitepoint.date = matplotlib.dates.num2date(t)
							subsatellitepoint.lon = tle_rec.sublong
							subsatellitepoint.lat = tle_rec.sublat
							tle_rec.compute(subsatellitepoint)
							altitude = tle_rec.range
							with open('../Data/OEs and LLAs/'+str(satcat)+'.csv', 'a') as csvfile:
								writer = csv.writer(csvfile)
								writer.writerow([str(matplotlib.dates.num2date(t)), line1[18:32], eccentricity, semimajor, inclination, RAAN, argperi, meananomaly, trueanomaly, latitude, longitude, altitude])
								print("Date:", str(matplotlib.dates.num2date(t))[0:10], "; Satcat #:", satcat, "-- Included")
						except (ValueError, RuntimeError):
							# with open('../Data/LLAs/'+str(satcat)+'.csv', 'a') as csvfile:
							# 	writer = csv.writer(csvfile)
							# 	writer.writerow([int(t)])
							print("Date:", str(matplotlib.dates.num2date(t))[0:10], "; Satcat #:", satcat, "-- Excluded (ValueError or RuntimeError)")
		else:
			print("Date:", str(matplotlib.dates.num2date(t))[0:10], "; Satcat #:", satcat, "-- Excluded (invalid timestep)")

	

	print("OEs and LLAs file created for satellite #", satcat)