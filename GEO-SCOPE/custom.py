import numpy as np
import csv
from datetime import datetime
from geoscope_util import contract
from search_parameters import study_start_date as start
from search_parameters import study_stop_date as stop
from search_parameters import data_directories as data_dir


class calculate_dr:
    def __init__(self, lon, timestep):
        self.ts_per_day = int(24*3600/timestep)
        self.by_phase = self.calc_by_phase(lon) # used to detect ID nodes
        self.by_mean = self.calc_by_mean(lon) # used to detect ED nodes
    
    def calc_by_phase(self,lon):
        dr = []
        for i in range(0,int(self.ts_per_day)):
            dr.append(np.abs(lon[i]-np.mean(lon[0:int(self.ts_per_day)])))
        for i in range(int(self.ts_per_day),len(lon)):
            dr.append(np.abs(lon[i]-lon[i-int(self.ts_per_day)]))
        return dr
    
    def calc_by_mean(self,lon):
        dr = [np.abs(np.mean(lon[self.ts_per_day:2*self.ts_per_day])
                       -np.mean(lon[0:self.ts_per_day]))]
        for i in range(1,self.ts_per_day):
            dr.append(np.abs(np.mean(lon[i:i+self.ts_per_day])
                             -np.mean(lon[0:self.ts_per_day])))
        for i in range(self.ts_per_day,len(lon)-self.ts_per_day):
            dr.append(np.abs(
                np.mean(lon[i-self.ts_per_day:i+self.ts_per_day]) 
                - np.mean(lon[i:int(i+self.ts_per_day)])))
        for i in range(len(lon)-self.ts_per_day,len(lon)):
            dr.append(np.abs(np.mean(lon[i:])
                             -np.mean(lon[len(lon)-self.ts_per_day:len(lon)])))
        return dr

def load_tle_data(satcat):
    num_duplicate_rows = 0
    times = []
    lon = []
    alt = []

    def inStudy(t):
        if start is None and stop is None: return True
        elif start is not None and stop is not None: return start <= t <= stop
        elif start is None: return t <= stop
        elif stop is None: return start <= t

    with open(data_dir.ephems + satcat + ".csv", encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=",")
        next(reader)
        for row in reader:
            if len(row) > 0:
                tr = datetime.fromisoformat(row[0])
                if inStudy(tr):
                    if len(times)>0:
                        if tr != times[-1]: 
                            times.append(tr)
                            lon.append(float(row[10])) # (-180,180)
                            alt.append(float(row[11])) # meters
                        else: num_duplicate_rows += 1
                    else:
                        times.append(tr)
                        lon.append(float(row[10]))
                        alt.append(float(row[11]))

    if len(times) > 0 and times[-1] is not None:
        timestep = (times[1]-times[0]).total_seconds()
        drift_rate = calculate_dr(lon,timestep)
        return [np.array(times),
                np.array(lon),
                np.array(alt),
                timestep,
                drift_rate]
    else: return None

def load_sim_data(satcat):
    num_duplicate_rows = 0
    times = []
    lon = []
    alt = []
    with open(data_dir.ephems + satcat + ".csv", encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=",")
        next(reader)
        for row in reader:
            if len(row) > 0:
                tr = datetime.fromisoformat(row[0])
                if len(times)>0:
                    if tr > times[-1]: 
                        times.append(tr)
                        lon.append(contract(float(row[8]))["180"]) # (-180,180)
                        alt.append(float(row[9])) # meters
                    else: num_duplicate_rows += 1
                else:
                    times.append(tr)
                    lon.append(contract(float(row[8]))["180"])
                    alt.append(float(row[9]))
    if len(times) > 0 and times[-1] is not None:
        if np.max(lon) > 180: print("WARNING: longitudes exceed 180 degrees")
        timestep = (times[1]-times[0]).total_seconds()
        drift_rate = calculate_dr(lon,timestep)
        return [np.array(times),
                np.array(lon),
                np.array(alt),
                timestep,
                drift_rate]
    else: return None
