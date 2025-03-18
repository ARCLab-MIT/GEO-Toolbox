'''
Publish dedicated repo on personal GitHub & add folder to GEO toolbox
'''
import csv
import numpy as np
from datetime import datetime, timezone, timedelta
import sys
import yaml
from plot_longitudes import plot_longitudes, contract, plot_londr
from custom import load_tle_data as load_LLA_data
from geoscope_util import satellite_history, cluster_history
from find_data import TLEs, SIMs, Cluster_History
import time

global debug; debug = False # Controls debug print statements
global te_fcs, te_ct
te_fcs = 0; te_ct = 0
############################################################################################################
# User-defined search parameters
MAX_BAND_SEPARATION = 0.8   # Longitude band in degrees for short-term check -> ONLY USED FOR CLUSTER CHECK
MAX_GEO_ALTITUDE = 35900000.0  # Maximum allowable altitude (meters) for GEO satellites
MIN_DAYS_IN_BAND = 5  # Minimum number of consecutive days within the band
MAX_LONGITUDE_VARIATION = 1.2  # Max allowable longitude variation (degrees) over time
VARIATION_CHECK_PERIOD = 30  # Period over which longitude variation is checked (in days)
LONGITUDE_SHIFT_THRESHOLD = 1.0  # Threshold in degrees for a longitudinal-shift maneuver
# TODO: add to node plot function: in slot vs not in slot with background color-coded accordingly
# TODO: add plot sat class method @ (plot single sat longitude signal and nodes from slots.yaml without running cluster search) -> can be in separate file
# TODO: make it simpler to switch between sources
# TODO: finish retrieve_last_cluster_state and cluster_history.load functions
# TODO: implement additional retirement checks
# TODO: add minimum altitude check for subsync
# TODO: add additional ID check logic for slow drifters
# TODO: fix export_current_cluster_states to only export most recent states
############################################################################################################
def run_cluster_search(data_dir=None,
                       print_clusters=True,  print_slots=True,
                       save_clusters=False,  save_slots=False,
                       STUDY_START=None,     STUDY_STOP=None,
                       MAX_DRIFT_RATE=None,  MAX_MEAN_DRIFT=None):
    '''
    Search for satellite slots and clusters between the STUDY_START and STUDY_STOP dates.
    File output methods are called here.
    '''
    global tstart
    tstart = time.perf_counter()
    tstart0 = tstart
    data_dir = TLEs if data_dir is None else data_dir

    ################ RUN ################
    # initialize cluster search parameters
    results = catalog_search(MAX_DRIFT_RATE,
                              MAX_MEAN_DRIFT,
                              MIN_DAYS_IN_BAND,
                              MAX_LONGITUDE_VARIATION,
                              VARIATION_CHECK_PERIOD,
                              MAX_BAND_SEPARATION,
                              MAX_GEO_ALTITUDE)
    
    # load satellite data
    results.load_satellites(data_dir,
                             STUDY_START,
                             STUDY_STOP)
    
    # search for slots
    tstart = time.perf_counter()
    results.find_slots()
    export_saterrors() # export satellites with no data
    tnow = time.perf_counter()
    print(f"Generated slots for {len(results.catalog)} / {len(results.catalog)} satellite histories in {round((tnow-tstart)/60,3)} minutes")
    if print_slots: results.print_satellite_events()
    if save_slots: results.export_satellite_histories(data_dir.slots)

    # search for clusters
    tstart = time.perf_counter()
    print(".\nSearching for clusters...")
    results.find_clusters()
    print("   ",len(results.clusters)," found in",round((time.perf_counter()-tstart)/60,3),"minutes")
    ############## EXPORTS ##############
    # if type(print_clusters) is bool:
    #     if print_clusters:
    #         results.print_summary_of_clusters()
    # else: results.print_cluster_timelines()
    if print_clusters: results.print_cluster_timelines()
    if save_clusters: 
        results.export_cluster_annotations(data_dir.clusters)
        results.export_current_cluster_states(data_dir.save4later)

    ################ FIN ################
    print(div)
    tend = time.perf_counter()
    print((tend-tstart0)/60.0,"minutes")
    return results

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

class catalog_search:
    def __init__(self,max_dr:float,
                 maxmn_dr:float,
                 min_time:float,
                 lon_var:float,
                 t_var:float,
                 lon_sep:float,
                 max_alt:float):
        
        # Search Parameters
        global phase_dr_max, mean_dr_max, min_slot_time, max_band_size, lookback, slot_size, geo_alt
        phase_dr_max=max_dr # initially set to 0.1 degrees
        mean_dr_max = maxmn_dr # initially set to 0.1 degrees
        min_slot_time=min_time # initially set to 1 day
        max_band_size=lon_var # initially set to 2 degrees
        lookback = t_var # initially set to 30 days
        slot_size=lon_sep # initially set to 0.8 degrees
        geo_alt=max_alt # initially set to 36000000 meters
        self.start = None
        self.stop = None

        # Search Results
        self.catalog = {} # sats to search
        self.catdex = []
        self.clusters = [] # active & inactive clusters
        # Helper Variables
        self.cluster = None
        self.cdex = None
        self.new = True  

    def load_satellites(self,data_dir,  # longitudes assumed to be -180 to 180 degrees, but contract function can be used to convert from 0-360
                        start=None,
                        stop=None):
        '''
        Loads satellite data for each satcat in SATCATS_FILE. Each satellite is stored in the 
        clustersearch.catalog list as a satellite_history object, complete with its astrometric data and 
        slot history.

        Support for additional data structures may be added via load_tle_data functions like the ones directly below.
        '''
        if start is not None: start = timestamp(start)
        if stop is not None: stop = timestamp(stop)

        satcats = []
        with open(data_dir.satcats, 'r',encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                satcats.append(str(row[0]))

        print(".")

        i = 1
        tnow = None
        for satcat in satcats:
            data = load_LLA_data(satcat)
            if data is not None: 
                satellite = satellite_history(satcat)
                satellite.timestamps = data[0]
                satellite.lon = data[1]
                satellite.alt = data[2]
                satellite.timestep = data[3]
                satellite.dr = data[4]
                self.catalog[satcat] = satellite
                self.catdex.append(satcat)
                if start is None:
                    ti = satellite.timestamps[0]
                    start = ti if ti < start else start
                if stop is None:
                    tf = satellite.timestamps[-1]
                    stop = tf if tf > stop else stop
            else: 
                sat_errors.append(satcat)
                debug_print(f"{satcat} has no data within the study period")
            tnow = time.perf_counter()
            print(f"Loading satellite {i} / {len(satcats)}, time ellapsed: {round((tnow-tstart)/60,1)} [min]",end="\r")
            i += 1
        # print(f"Loading satellite {i} / {len(satcats)}, time ellapsed: {round((tnow-tstart)/60,1)} [min]   ")
        self.start = start; self.stop = stop
    
    @classmethod
    def load_truth_slots(cls,
                         data_dir,
                        STUDY_START,
                        STUDY_STOP,
                        MAX_DRIFT_RATE, #0.021,
                        MAX_MEAN_DRIFT): #0.1):
        global tstart
        tstart = time.perf_counter()
        C = cls(MAX_DRIFT_RATE,
                MAX_MEAN_DRIFT,
                MIN_DAYS_IN_BAND,
                MAX_LONGITUDE_VARIATION,
                VARIATION_CHECK_PERIOD,
                MAX_BAND_SEPARATION,
                MAX_GEO_ALTITUDE) #0.1):
        truth_nodes = yaml.safe_load(open(data_dir.truth).read())

        def make_mode(ti,sat,cstr):
            mode = {}
            mode["exit"] = None
            mode["lon"] = np.mean(sat.lon[:])
            mode["lon<"] = np.max(sat.lon[:])
            mode["lon>"] = np.min(sat.lon[:])
            mode["alt"] = None
            mode["alt<"] = None
            mode["alt>"] = None
            mode["dr p>"] = None
            mode["dr p<"] = None
            mode["dr m>"] = None
            mode["dr m<"] = None
            mode["dr m"] = None
            mode["dr p"] = None
            mode["satnum"] = sat.satnum
            mode["timeframe"] = [sat.timestamps[0],sat.timestamps[-1]]
            mode["entry"] = None if ti is None else ti
            mode["class"] = cstr
            mode["orbit"] = "GEO"
            return mode
        scount = 1
        for satcat in truth_nodes:
            print(f"Loading satellite {scount} / {len(truth_nodes)}",end="\r")
            scount += 1
            s = truth_nodes[satcat]
            sat = C.satellite_history(satcat)
            sat.timestamps = []
            sat.lon = []
            sat.alt = []
            sat.dr = None
            sat.slots = []
            sat.modes = []
            sat.events = []
            sat.retired = False

            with open(data_dir.ephems + satcat + ".csv", encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=",")
                next(reader)
                for row in reader:
                    if len(row) > 0:
                        tr = datetime.fromisoformat(row[0])
                        if dir == TLEs:
                            if datetime(2021, 7, 1,tzinfo=timezone.utc) <= tr <= datetime(2021, 12, 31,tzinfo=timezone.utc):
                                if len(sat.timestamps) == 0:
                                    sat.timestamps.append(tr)
                                    sat.lon.append(float(row[10]))
                                elif tr != sat.timestamps[-1]:
                                    sat.timestamps.append(tr)
                                    sat.lon.append(float(row[10]))  # Assuming longitude is in the 9th column
                        elif len(sat.timestamps) == 0:
                            sat.timestamps.append(tr)
                            sat.lon.append(float(row[8]))
                        elif tr != sat.timestamps[-1]:
                            sat.timestamps.append(tr)
                            sat.lon.append(float(row[8]))
            if len(sat.timestamps) > 1:
                sat.timestep = (sat.timestamps[1] - sat.timestamps[0]).total_seconds()
                # sat.dr = calculate_dr(sat.lon, sat.timestep)

            if s["M0"] == "in slot": m = make_mode(sat.timestamps[0],sat,"in slot")
            elif s["M0"] == "drifting": m = make_mode(sat.timestamps[0],sat,"drifting")
            if s["Nodes"] is not None: 
                for node in s["Nodes"]:
                    m["exit"] = timestamp(node["time"])
                    sat.modes.append(m)
                    m = make_mode
                    if node["type"] == "ED": m = make_mode(timestamp(node["time"]),sat,"in slot")
                    elif node["type"] == "ID": m = make_mode(timestamp(node["time"]),sat,"drifting")
            m["exit"] = sat.timestamps[-1]
            sat.modes.append(m)
            m = None
            for m in sat.modes:
                if m["class"] == "in slot":
                    sat.slots.append(m)
            C.catalog[satcat] = sat
            C.catdex.append(satcat)
        return C
    
    def find_slots(self):
        print(".")
        i = 1
        for satnum in self.catalog:
            sat = self.catalog[satnum]
            sat.create_PoL()
            tnow = time.perf_counter()
            print(f"Generating PoL {i} / {len(self.catalog)}, time ellapsed: {round((tnow-tstart)/60,1)} [min]",end="\r")
            i += 1

    def retrieve_last_cluster_state(self):
        self.last_update = yaml.safe_load(open("filename").read())
        for cluster in self.last_update:
            satellites = []
            # for satnum in self.last_update[cluster]["Satellites"]"cluster"

    def find_clusters(self):
        # t291 = time.perf_counter()
        for i in range(len(self.catalog)):
            sati = self.catalog[self.catdex[i]]
            print(f"Processing {i+1} / {len(self.catalog)} satellites",end="\r")
            # Skip satellites with no slots
            if len(sati.slots) < 1: continue
            self.cdex = None
            scount = 1
            for si in sati.slots:
                print(f"Processing {i+1} / {len(self.catalog)} satellites, {scount} / {len(sati.slots)} slots",end="\r")
                scount += 1
                self.cluster = None
                if self.exists(si):
                    self.new = False
                    self.set_cdex(si)
                    self.cluster = self.clusters.pop(self.cdex)
                    self.cluster.slots.append(si)
                    self.cluster.resident_history.append(self.catdex[i])
                    # self.cluster.merge(self.clusters[self.cdex])
                else:
                    self.new = True
                    for j in range(len(self.catalog))[i+1:]:
                        satj = self.catalog[self.catdex[j]]
                        if len(satj.slots)<1: continue
                        for sj in satj.slots:
                            if self.does_overlap(si,sj):
                                if self.is_clustered(si,sj):
                                    if self.exists(sj):
                                        self.set_cdex(sj)
                                        self.new = False
                                        if self.cluster is None:
                                            self.cluster = self.clusters.pop(self.cdex)
                                            self.cluster.slots.append(si)
                                            self.cluster.resident_history.append(self.catdex[i])
                                        else:
                                            self.cluster.merge(self.clusters[self.cdex])
                                    elif self.cluster is None:
                                        self.cluster = cluster_history()
                                        self.cluster.slots.extend([si,sj])
                                        self.cluster.resident_history.extend([self.catdex[i], self.catdex[j]])
                                    else:
                                        self.cluster.slots.append(sj)
                                        self.cluster.resident_history.append(self.catdex[j])
                # t327 = time.perf_counter()
                # te_fcs += t327-t291
                if self.cluster is not None:
                    self.clusters.append(self.cluster)

        print(f"Generated {len(self.clusters)} clusters in {round((time.perf_counter()-tstart)/60,1)} minutes")
        ccount = 1
        for cluster in self.clusters:
            print(f"Processing {ccount} / {len(self.clusters)} clusters",end="\r")
            ccount += 1
            cluster.create_timeline()        
            # print(f"{i+1}/{len(self.catalog)} satellites processed {"."*(i%5)}",end="\r")

    def does_overlap(self,si,sj):
        i0 = si["timeframe"][0] if si["entry"] is None else si["entry"]
        i1 = si["timeframe"][1] if si["exit"] is None else si["exit"]
        j0 = sj["timeframe"][0] if sj["entry"] is None else sj["entry"]
        j1 = sj["timeframe"][1] if sj["exit"] is None else sj["exit"]
        if (j0<=i0<=j1<=i1):
            return True
        elif (i0<=j0<=i1<=j1):
            return True
        elif ((i0<=j0) and (j1<=i1)):
            return True
        elif((j0<=i0) and (i1<=j1)):
            return True
        else:
            return False
    
    def is_clustered(self,si,sj):
        i0 = si["lon>"]
        i1 = si["lon<"]
        j0 = sj["lon>"]
        j1 = sj["lon<"]

        if np.abs(i1-i0) > max_band_size:
            return False
        if np.abs(j1-j0) > max_band_size:
            return False
        if (i1>j1>i0>j0):
            return True
        elif (i0<j0<i1<j1):
            return True
        elif ((i1>j1) and (i0<j0)):
            return True
        elif ((np.abs(i0-j1)<=slot_size) or (np.abs(j0-i1)<=slot_size)):
            return True
        else:
            return False
        
    def set_cdex(self,si):
        if si["entry"] is None: # CHANGED THIS
            for c in range(len(self.clusters)):
                for slot in self.clusters[c].slots: # FIX THIS FOR RETRIEVE_LAST_CLUSTER_STATE
                    if (slot["timeframe"][0] == slot["timeframe"][1]) and (slot["satnum"] == si["satnum"]):
                        self.cdex = c
                        return
        for c in range(len(self.clusters)):
            if si in self.clusters[c].slots:
                self.cdex = c
                return
        sys.exit("ERROR: Cannot set cdex because satellite is not clustered")

    def exists(self,si):
        if si["entry"] is None: # CHANGED THIS
            for cluster in self.clusters:
                for slot in cluster.slots: # FIX THIS FOR RETRIEVE_LAST_CLUSTER_STATE
                    if (slot["timeframe"][1] == slot["timeframe"][0]) and (slot["satnum"] == si["satnum"]):
                        return True
        for cluster in self.clusters:
            if si in cluster.slots:
                return True
        return False

    def slot_nodes(self, plot_dir=None): # return list of datetimes
        timestamps = []
        for satnum in self.catalog.keys():
            sat = self.catalog[satnum]
            sat_timestamps, ncolors = sat.nodes()
            timestamps += sat_timestamps
            if plot_dir is not None:
                data2plot = {satnum: np.vstack([np.array(sat.timestamps), np.array(sat.lon), np.array(sat.dr.by_phase), np.array(sat.dr.by_mean), np.array(sat.alt)])}    
                plot_londr(data2plot,
                                None,
                                None,
                                lon_range=[np.min(sat.lon)-1.25, np.max(sat.lon)+1.25],
                                nodes=sat_timestamps,
                                ncolors=ncolors,
                                plot_alt=True)
        return timestamps

    def cluster_nodes(self,plot_dir=None): # return list of datetimes
        timestamps = []
        for cluster in self.clusters:
            ctimes = []
            ccolors = []
            data2plot = {}
            sats = cluster.get_all_sats()
            for event in cluster.events:
                if (event["type"] == "entered"):
                    ctimes.append(event["timestamp"])
                    ccolors.append(GREEN)
                elif (event["type"] == "exited"):
                    ctimes.append(event["timestamp"])
                    ccolors.append(PURPLE)
            for sat in sats:
                data2plot[sat] = np.vstack([np.array(self.catalog[sat].timestamps), np.array(self.catalog[sat].lon)])
            timestamps += ctimes
            if plot_dir is not None: 
                if len(ctimes) == 0: ctimes = None
                if len(ccolors) == 0: ccolors = None
                debug_print(f"plotting cluster {cluster.names[len(cluster.names)-1]}")
                plot_longitudes(data2plot,
                                plot_dir,
                                "Cluster"+str(cluster.names[len(cluster.names)-1]),
                                lon_range=[cluster.states[0].longitude-1.25,cluster.states[0].longitude+1.25],
                                nodes=ctimes,
                                ncolors=ccolors)
        return timestamps
    
    def print_cluster_timelines(self):
        div = ""
        for i in range(14): div += "__"
        print(div+"\nCLUSTER SEARCH:")
        # print(len(self.clusters),"clusters found")
        for cluster in self.clusters:
            print(".\nCluster @",round(float(cluster.names[len(cluster.names)-1]),1),":",len(cluster.events),"events")
            cluster.print()
            print(".")
    
    def print_summary_of_clusters(self):
        div = ""
        for i in range(14): div += "__"
        print(div+"\nSUMMARY:")
        print(len(self.catalog),"satellites loaded")
        print(len(self.clusters),"clusters found")
        print(len(self.slot_nodes()),"nodes found")
        L = len(self.clusters)
        i = 1
        for cluster in self.clusters:
            print(f"{i}/{L} Cluster @{round(float(cluster.names[-1]),1)}: {cluster.get_all_sats()}")
            print(f"      t0: {str(self.start)[:19]}        (study start)")
            print(f"      ti: {str(cluster.states[0].init_time)[:19]}        (cluster formation)")
            print(f"      tf: {str(cluster.last_seen)[:19]}")
            print(f"  active: {"yes" if cluster.active else "no"}")
            print(f"  events: {len(cluster.events)}")
            i += 1
            print(".")

    def print_satellite_events(self):
        div = ""
        for i in range(14): div += "__"
        print(div+"\nSATELLITE EVENTS:")
        for satnum in self.catalog:
            self.catalog[satnum].print()
            print(".")
    
    def export_cluster_annotations(self,ofile):
        export_format = {}
        for cluster in self.clusters:
            members = cluster.get_all_sats()
            # if cluster.active: members = cluster.states[len(cluster.states)-1].satnums
            current_name = str(round(float(cluster.names[len(cluster.names)-1]),1))
            events = {}
            if cluster.states[0].init_time is None:
                events[str(self.start)[:19]] = f"existing cluster @{cluster.names[0]} {cluster.states[0].satnums}"
                for ts, estring in cluster.print(to_yaml=True).items():
                    events[ts] = estring
            else: events = cluster.print(to_yaml=True)
            export_format[current_name] = {
                "active":cluster.active,
                "ti":cluster.states[0].init_time,
                "tf":cluster.last_seen,
                "Members":members,
                "Events":events,
            }
        yaml.dump(export_format,open(ofile,"w"),default_flow_style=False, sort_keys=False)

    def export_current_cluster_states(self,ofile): 
        '''
        Preserve current state of all active clusters.
        Cluster states are stored in YAML format and
        can be used to initialize a future cluster
        search.
        '''
        data = {}
        for cluster in self.clusters:
            data[cluster.names[len(cluster.names)-1]] = cluster.export()
        yaml.dump(data,open(ofile,"w"),default_flow_style=False, sort_keys=False)

    def export_satellite_histories(self,ofile):
        slot_export = {}
        for satnum in self.catalog:
            slot_export[satnum] = self.catalog[satnum].export_format()
        yaml.dump(slot_export,open(ofile,"w"),default_flow_style=False, sort_keys=False)

# if __name__=='__main__':
#     main()

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
sat_errors = []
def export_saterrors():
    with open(Cluster_History+"sat_errors.txt","w") as f:
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
return_validity = True # just for readability

##############################################################################