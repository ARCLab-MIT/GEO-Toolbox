import os
path = os.path.abspath("./arclab/GEOToolbox")
import numpy as np
from datetime import datetime, timedelta, timezone
import csv
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
class history:
    def __init__(self,satcat: int,t1: datetime,t2: datetime):
        '''
        satcat -> 5 digit norad ID\n
        t1 -> first timestamp\n
        t2 -> last timestamp\n
        '''
        
        print()
        print(path)
        print()

        self.satcat = str(satcat)
        self.firsttime = t1
        self.lasttime = t2
        self.OE_arr = None
        self.LLA_arr = None
        self.CleanLLA_arr = None
        self.datetimes = None
        self.timestep = 0
        self.scEpoch = None

    def OE_LLA(self):
        '''
        Retrieves the OE_LLA data for the satcat over the pre-initialized timeframe\n
        '''
        times = []
        scEpoch = []
        ecc = []
        a = []
        inc = []
        raan = []
        argp = []
        nu = []
        fa = []
        lat = []
        lon = []
        alt = []
        Cleanlon = []
        Cleanlat = []
        with open(path+"/Data/OEs and LLAs/" + self.satcat + ".csv", encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=",")
            header = next(reader)
            # for i in range(len(header)):
            #     print("col "+str(i)+": "+header[i])
            for row in reader:
                time = datetime.fromisoformat(row[0])
                epoch = row[1]
                if int(epoch[0:2])<57:
                    year = int("20"+epoch[0:2])
                else:
                    year = int("19"+epoch[0:2])
                day_snippet = epoch[2:12]
                epoch = datetime(year,1,1,0,0,0,tzinfo=timezone.utc)+timedelta(days=float(day_snippet))
                if (time >= self.firsttime)&(time <= self.lasttime):
                    if (len(times) > 0):
                        if (time != times[-1]):
                            times.append(time)
                            scEpoch.append(float((time-epoch).total_seconds()/(60*60)))
                            ecc.append(float(row[2]))
                            a.append(float(row[3]))
                            inc.append(float(row[4]))
                            raan.append(float(row[5]))
                            argp.append(float(row[6]))
                            nu.append(float(row[7]))
                            fa.append(float(row[8]))
                            lat.append(float(row[9]))
                            lon.append(float(row[10]))
                            alt.append(float(row[11]))
                    else:
                            times.append(time)
                            scEpoch.append(float((time-epoch).total_seconds()/(60*60)))
                            ecc.append(float(row[2]))
                            a.append(float(row[3]))
                            inc.append(float(row[4]))
                            raan.append(float(row[5]))
                            argp.append(float(row[6]))
                            nu.append(float(row[7]))
                            fa.append(float(row[8]))
                            lat.append(float(row[9]))
                            lon.append(float(row[10]))
                            alt.append(float(row[11]))
        self.scEpoch = np.array(scEpoch)
        self.datetimes = np.array(times)
        self.OE_arr = np.vstack([
            np.array(times),
            np.array(ecc),
            np.array(a),
            np.array(inc),
            np.array(raan),
            np.array(argp),
            np.array(nu),
            np.array(fa)
        ])
        self.LLA_arr = np.vstack([
            np.array(times),
            np.array(lon),
            np.array(lat),
            np.array(alt)
        ])
        Cleanlon = np.array(lon)
        Cleanlat = np.array(lat)
        for i in range(1,len(lon)):
            lon0 = Cleanlon[i-1]
            lon1 = Cleanlon[i]
            lat0 = Cleanlat[i-1]
            lat1 = Cleanlat[i]
        
            if (lon0>=179)&(np.abs(lon0-lon1)>=179):
                Cleanlon[i] = 360 + lon1
            elif (lon0<=-179)&(np.abs(lon0-lon1)>=179):
                Cleanlon[i] = -360 + lon1
                
            if (lat0>179)&(np.abs(lat0-lat1)>=179):
                Cleanlat[i] = 360 + lat1
            elif (lat0<-179)&(np.abs(lat0-lat1)>=179):
                Cleanlat[i] = -360 + lat1

        self.CleanLLA_arr = np.vstack([
            np.array(times),
            np.array(Cleanlon),
            np.array(Cleanlat),
            np.array(alt)
        ])
                # Find the data's timestep
        i = 1
        while self.timestep == 0:
            self.timestep = (times[i]-times[0]).total_seconds()
            i += 1


    def OE(self,t1: datetime = None,t2: datetime = None):
        '''
        Returns an array of the orbital elements over the specified timeframe\n
        Uses the pre-initialized timeframe if no dates are given\n
        '''
        if self.OE_arr is None:
            self.OE_LLA()
        if ((t1 is None)&(t2 is None)):
            return self.OE_arr
        t1 = self.firsttime if t1 is None else t1
        t2 = self.lasttime if t2 is None else t2
        t = []
        ecc = []
        a = []
        inc = []
        raan = []
        argp = []
        nu = []
        fa = []
        for step in self.OE_arr:
            if (step[0]>=t1)&(step[0]<=t2):
                t.append(self.OE_arr[0])
                ecc.append(self.OE_arr[1])
                a.append(self.OE_arr[2])
                inc.append(self.OE_arr[3])
                raan.append(self.OE_arr[4])
                argp.append(self.OE_arr[5])
                nu.append(self.OE_arr[6])
                fa.append(self.OE_arr[7])
        OE_trimmed = np.vstack([
            np.array(t),
            np.array(ecc),
            np.array(a),
            np.array(inc),
            np.array(raan),
            np.array(argp),
            np.array(nu),
            np.array(fa)
        ])
        return OE_trimmed
        

    def LLA(self,t1: datetime = None,t2: datetime = None):
        '''
        Returns an array of the geographic coordinates over the specified timeframe\n
        Uses the pre-initialized timeframe if no dates are given\n
        '''
        if self.LLA_arr is None:
            self.OE_LLA()
        if ((t1 is None)&(t2 is None)):
            return self.LLA_arr
        t1 = self.firsttime if t1 is None else t1
        t2 = self.lasttime if t2 is None else t2
        t = []
        lon = []
        lat = []
        alt = []
        for step in self.LLA_arr:
            if (step[0]>=t1)&(step[0]<=t2):
                t.append(self.LLA_arr[0])
                lon.append(self.LLA_arr[1])
                lat.append(self.LLA_arr[2])
                alt.append(self.LLA_arr[3])
        LLA_trimmed = np.vstack([
            np.array(t),
            np.array(lon),
            np.array(lat),
            np.array(alt)
        ])
        return LLA_trimmed
    
    def CleanLLA(self,t1: datetime = None,t2: datetime = None):
        '''
        Returns an array of the geographic coordinates over the specified\n
        timeframe with continuous latitudes and longitudes in units of degrees\n
        Uses the pre-initialized timeframe if no dates are given\n
        '''
        if self.CleanLLA_arr is None:
            self.OE_LLA()
        if ((t1 is None)&(t2 is None)):
            return self.CleanLLA_arr
        t1 = self.firsttime if t1 is None else t1
        t2 = self.lasttime if t2 is None else t2
        t = []
        lon = []
        lat = []
        alt = []
        for step in self.CleanLLA_arr:
            if (step[0]>=t1)&(step[0]<=t2):
                t.append(self.CleanLLA_arr[0])
                lon.append(self.CleanLLA_arr[1])
                lat.append(self.CleanLLA_arr[2])
                alt.append(self.CleanLLA_arr[3])
        CleanLLA_trimmed = np.vstack([
            np.array(t),
            np.array(lon),
            np.array(lat),
            np.array(alt)
        ])
        return CleanLLA_trimmed

    def getTLEepochs(self,start: datetime,end: datetime):
        def file_len(fname):
            with open(fname) as f:
                lines = len(f.readlines())
            return lines
        index = []
        for a in np.arange(0,file_len(path+'/Data/TLEs/'+str(self.satcat)+'.txt'),2):
            index.append(a)
        l1 = []
        l2 = []
        dates = []
        with open(path+'/Data/TLEs/'+str(self.satcat)+'.txt') as g: 
            lines = g.readlines()
            for x in index:
                line1 = str(lines[x].strip())
                line2 = str(lines[x+1].strip())
                year_snippet = line1[18:20]
                if int(year_snippet)<57:
                    year = int("20"+year_snippet)
                else:
                    year = int("19"+year_snippet)
                day_snippet = line1[20:32]
                t = datetime(year,1,1,0,0,0,tzinfo=timezone.utc)+timedelta(days=float(day_snippet))
                if (t >= start)&(t <= end):
                    l1.append(line1)
                    l2.append(line2)
                    dates.append(t)
        dates = np.flip(np.array(dates))
        lon = []
        
        for i in range(len(dates)):
            index = len(self.datetimes)-1
            min = 48*60*60
            for j in range(len(self.datetimes)):
                diff = (self.datetimes[j] - dates[i]).total_seconds()
                if diff < min:
                    min = diff
                    index = j
            lon.append(self.CleanLLA_arr[index][1])
        return np.array(dates),np.array(lon)

    def PlotEpochColors(self,datetimes,data,t1: datetime = None,t2: datetime = None, title: str = None):
        '''
        Generates a scatter plot of a data set with markers color-coded according to\n
        the datetimes' distances (in hours) from or to the nearest TLE epoch.
        '''
        t = []
        y = []
        scEpoch = []
        if ((t1 is not None) or (t2 is not None)): 
            t1 = self.firsttime if t1 is None else t1
            t2 = self.lasttime if t2 is None else t2
            for i in range(len(datetimes)):
                if (datetimes[i]>=t1)&(datetimes[i]<=t2):
                    t.append(datetimes[i])
                    y.append(data[i])
                    scEpoch.append(np.abs(self.scEpoch[i]))
        else:
            t = datetimes
            y = data
            scEpoch = np.abs(self.scEpoch)
        epochs,lonTLE = self.getTLEepochs(t1,t2)
        cmap = ListedColormap(["green", "gold", "crimson", "purple" ])
        nodes = np.array([0.0, 12.0, 24.0, 36.0, 48.0])
        norm = BoundaryNorm(boundaries=nodes, ncolors=5, extend='max')

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ephems = ax.scatter(t, y, s=1, c=scEpoch, cmap=cmap, norm=norm, marker='.')
        # tles = ax.scatter(epochs,lonTLE, s=2, marker='<') # TODO
        fig.colorbar(ephems,label="Hours From Nearest Epoch")
        if title is not None:
            fig.suptitle(title)
        plt.show()

    # def rv(self,t1: datetime = None,t2: datetime = None):
    #     '''
    #     Returns an array of the position and velocities over the specified timeframe\n
    #     Uses the pre-initialized timeframe if no dates are given\n
    #     '''
    #     if self.rv_arr == None:
    #         # calculate self.rv_arr
    #         pass
        
    #     if (t1 != None) or (t2 != None):
    #         #TODO: cut array to timeframe
    #         rv_trimmed = self.rv_arr
    #         return rv_trimmed
    #     else:
    #         return self.rv_arr

    # def dv(self,t1: datetime = None,t2: datetime = None):
    #     '''
    #     Returns the changes in velocity over the specified timeframe\n
    #     Uses the pre-initialized timeframe if no dates are given\n
    #     '''
    #     if self.dv_arr == None:
    #         # calculate self.dv_arr
    #         pass
        
    #     if (t1 != None) or (t2 != None):
    #         #TODO: cut array to timeframe
    #         dv_trimmed = self.dv_arr
    #         return dv_trimmed
    #     else:
    #         return self.dv_arr
