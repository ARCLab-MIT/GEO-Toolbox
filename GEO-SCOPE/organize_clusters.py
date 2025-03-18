import numpy as np
from geoscope_util import debug_print
from datetime import timedelta

class cluster_history:
    def __init__(self):
        self.active = False
        self.states = []
        self.resident_history = []
        self.slots = []
        self.names = []
        self.events = []
        self.first_active = None
        self.last_seen = None

    @classmethod
    def load(cls,name,cluster,sats):
        C = cls()
        s = 0
        for satellite in cluster["Satellites"]:
            satellite = {}
            s += 1
        return C
    
    class state:
        def __init__(self):
            # print("state initialized")
            self.longitude = None
            self.name = None
            self.init_time = None
            self.end_time = None
            self.slots = {}
            # self.metaData = {}
            self.satnums = []
            self.initialized = False
            self.active = False

        def new_slot(self, slot, t0=None):
            self.slots[slot["satnum"]] = slot
            if slot["satnum"] not in self.satnums:
                self.satnums.append(slot["satnum"])
            # self.metaData[slot["satnum"]] = satellite.metaData
            self.active = True if self.initialized else False
            if not self.initialized:
                self.init_time = None
                self.end_time = None
            self.initialized = True
            if (t0 is not None):
                self.init_time = t0
            if self.active: self.longitude = np.mean([self.slots[s]["lon"] for s in self.slots])

        def get_name(self,lons=None):
            def shorten(lon):
                return str(round(float(lon),1))
            # print("get_name:",np.mean(lons))
            if lons is not None:
                self.name = shorten(np.mean(lons))
                self.longitude = np.mean(lons)
                return self.name
            elif self.name is not None:
                return self.name
            elif self.longitude is not None:
                return shorten(self.longitude)
            else: return None

        def remove(self, satnum):
            # print("remove",satnum,[s for s in self.slots])
            if satnum in self.slots: self.slots.pop(satnum)
            else: debug_print(f"{satnum} not in slots")
            # else: print(satnum,"not in satellites")
            # self.metaData.pop(satnum)
            if satnum in self.satnums: self.satnums.remove(satnum)
            else: debug_print(f"{satnum} not in satnums")
            if len(self.satnums) == 0:
                self.initialized = False
            if len(self.satnums) == 1:
                self.active = False

    def get_all_sats(self):
        sats = []
        for state in self.states:
            sats.extend(state.satnums)
        return list(set(sats))
    
    def create_timeline(self):
        # t689 = time.perf_counter()
        debug_print("\nCreate timeline\n")
        self.states = []
        self.events = []
        state = self.state()
        timeline = []
        lons = []
        # Add slots (& sats, lons) with no entry to first state
        # first state is initialized when adding first slot
        # first state is active when adding second slot
        # Add entry event to timeline for all slots with entry
        # Add exit event to timeline for all slots with exit
        for i in range(len(self.slots)):
            slot = self.slots[i]
            sat = self.resident_history[i]
            if slot["entry"] is None: # add slot to first state
                state.new_slot(slot)
                lons.append(slot["lon"])
            else: # add slot entry to timeline
                timeline.append(
                    {
                        "time":slot["entry"],
                        "type":"entry",
                        "sat":sat,
                        "slot":slot
                    }
                )
            if slot["exit"] is not None: # add slot exit to timeline
                timeline.append(
                    {
                        "time":slot["exit"],
                        "type":"exit",
                        "sat":sat,
                        "slot":slot
                    }
                )
        timeline.sort(key = lambda x:x['time'])
        # if cluster already active, record initial state
        if state.active:
            self.new_state(state)
            self.names.append(state.get_name(lons))
        end_time = None
        # create new states for each entry/exit event
        for event in timeline:
            if event["type"] == "entry":
                if not state.initialized: # first sat, no cluster
                    state.new_slot(event["slot"])
                    lons.append(event["slot"]["lon"])
                    state.initialized = True; state.active = False; self.active = False
                elif state.initialized and (not state.active): # 2nd sat, cluster formed
                    state.new_slot(event["slot"],event["time"])
                    state.end_time = None
                    lons.append(event["slot"]["lon"])
                    self.names.append(state.get_name(lons))
                    self.new_entry(event,state)
                    self.new_cluster(event,state)
                    self.new_state(state)
                    state.initialized = True; state.active = True; self.active = True
                else:
                    state.new_slot(event["slot"])
                    self.new_entry(event,state)
                    lons.append(event["slot"]["lon"])
                    new_name = state.get_name(lons)
                    if self.names[-1] != new_name:
                        self.new_name(event,new_name,state)
                    self.new_state(state)
                    state.initialized = True; state.active = True; self.active = True
            elif event["type"] == "exit":
                if len(state.satnums) > 2:
                    self.new_exit(event,state)
                    state.init_time = event["time"]                        
                    state.remove(event["sat"])
                    if event["slot"]["lon"] in lons: lons.remove(event["slot"]["lon"])
                    new_name = state.get_name(lons)
                    if self.names[len(self.names)-1] != new_name:
                        self.new_name(event,new_name,state)
                    self.new_state(state)
                    state.initialized = True; state.active = True; self.active = True
                elif len(state.satnums) == 2:
                    self.new_exit(event,state)
                    state.init_time = event["time"]                        
                    state.end_time = event["time"]
                    end_time = event["time"]
                    state.remove(event["sat"])
                    if event["slot"]["lon"] in lons: lons.remove(event["slot"]["lon"])
                    self.empty(event,state)
                    self.new_state(state)
                    state.initialized = True; state.active = False; self.active = False
                elif len(state.satnums) == 1:
                    state.remove(event["sat"])
                    if event["slot"]["lon"] in lons: lons.remove(event["slot"]["lon"])
                    self.new_state(state)
                    state.active = False; state.initialized = False; self.active = False
                else: 
                    state.initialized = False
                    state.active = False
                    self.active = False

        self.last_seen = end_time
        if self.active and len(state.satnums) < 2:
            debug_print(f"{len(self.resident_history)}, {len(self.states)}")
            if len(self.events) > 0: debug_print(f"{self.events[-1]["satnum"]} {self.events[-1]["type"]} for {self.events[-1]["recipients"]}")
        elif self.active:
            lasttimes = []
            for s in state.slots:
                lasttimes.append(state.slots[s]["timeframe"][1])
            debug_print(f"lasttimes: {lasttimes}")  # Debug print statement
            if lasttimes:
                self.last_seen = np.max(np.array(lasttimes))
        # t797 = time.perf_counter()
        # te_ct += t797-t689
        # print(f"runtime: find_clusters: {te_fcs} [s], create_timeline: {te_ct} [s]")

    def merge(self,cluster):
        # print("merge")
        for i in range(len(cluster.slots)):
            slot = cluster.slots[i]
            sat = cluster.resident_history[i]
            if slot not in self.slots:
                self.slots.append(slot)
                self.resident_history.append(sat)
        for event in cluster.events:
            if event not in self.events:
                self.events.append(event)
        self.active = cluster.active or self.active
        if self.first_active is None: self.first_active = cluster.first_active
        elif cluster.first_active is None: pass
        else: self.first_active = cluster.first_active if cluster.first_active < self.first_active else self.first_active

    def new_state(self,state):
        # print("new state:")
        new_state = self.state()
        new_state.longitude = float(state.longitude) if state.longitude else None
        new_state.name = state.get_name()
        new_state.init_time = state.init_time
        new_state.end_time = state.end_time
        new_state.slots = {}
        for slot in state.slots:
            new_state.slots[slot] = state.slots[slot]
        # new_state.metaData = {}
        # for data in state.metaData:
        #     new_state.metaData[data] = state.metaData[data]
        new_state.satnums = list(set(state.satnums))
        new_state.initialized = bool(state.initialized)
        new_state.active = bool(state.active)
        self.states.append(new_state)

    def new_cluster(self,event,state):
        # print("new cluster",self.names[len(self.names)-1])
        self.events.append({
            "type":"formed",
            "timestamp":event["time"]+timedelta(seconds=1),
            "satnum":None,
            "@":self.names[len(self.names)-1],
            "recipients":set(state.satnums)
        })
        self.active = True
        self.first_active = event["time"]
    
    def new_entry(self,event,state):
        # print("new entry",event["sat"],"@"+str(self.names[len(self.names)-1]))
        self.events.append({
            "type":"entered",
            "timestamp":event["time"],
            "satnum":event["sat"],
            "@":self.names[len(self.names)-1],
            "recipients":set(state.satnums)
        })
        self.active = True

    def new_exit(self,event,state):
        # print("new exit",event["sat"],"@"+str(self.names[len(self.names)-1]), "on",str(event["time"])[0:10])
        self.events.append({
            "type":"exited",
            "timestamp":event["time"],
            "satnum":event["sat"],
            "@":self.names[len(self.names)-1],
            "recipients":set(state.satnums)
        })
    
    def empty(self,event,state):
        # print("empty @",self.names[len(self.names)-1])
        self.events.append({
            "type":"dissolved",
            "timestamp":event["time"]+timedelta(seconds=1),
            "satnum":None,
            "@":self.names[len(self.names)-1],
            "recipients":set(state.satnums)
        })
        self.active = False

    def new_name(self,event,new_name,state):
        # print("new name",self.names[len(self.names)-1],new_name)
        old_name = self.names[len(self.names)-1]
        self.names.append(new_name)
        self.events.append({
            "type":"renamed",
            "timestamp":event["time"]+timedelta(seconds=1),
            "satnum":None,
            "@":[old_name,new_name],
            "recipients":set(state.satnums)
        })
    
    def print(self,to_yaml=False): # print events for one cluster
        self.events.sort(key = lambda x:x['timestamp'])
        event_timeline = {}
        
        def print_or_export(ts,sms):
            if to_yaml:
                event_timeline[str(ts)[:19]] = sms
            else:
                print(str(ts)[:19])
                print("     ",sms)
        for event in self.events:
            if event["satnum"] is not None:
                text = [event["satnum"],event["type"],"cluster @"+event["@"],str(event['recipients'])]
                print_or_export(event["timestamp"],' '.join(text))
            elif event["type"] == "renamed":
                text = ["cluster @"+event["@"][0],event["type"],event["@"][1],str(event['recipients'])]
                print_or_export(event["timestamp"],' '.join(text))
            else:
                text = ["cluster",event["type"],"@"+event["@"],str(event['recipients'])]
                print_or_export(event["timestamp"],' '.join(text))
        if len(self.events) == 0:
            only_state = self.states[0]
            if not to_yaml:
                print("Cluster @"+only_state.get_name(),only_state.satnums)
                print("     No events")
                print("    ",len(set(self.resident_history)),"satellites in cluster:")
                for sat in set(self.resident_history):
                    print("          ",sat)
            else: print_or_export(self.last_seen,f"{only_state.satnums} last seen in cluster @{only_state.name}")
        elif self.active:
            final_state = self.states[len(self.states)-1]
            print_or_export(self.last_seen,f"{final_state.satnums} last seen in cluster @{final_state.get_name()}")

        return event_timeline
    
    def export(self): # export cluster history as dictionary
        self.events.sort(key = lambda x:x['timestamp'])
        cluster_export = {}
        cluster_export["Active"] = self.active
        sf = self.states[-1]
        state_slots = {}
        for slot in sf.slots:
            sdict = sf.slots[slot]
            state_slots[sdict["satnum"]] = {
                "timeframe":[str(t) for t in sdict["timeframe"]],
                "entry":sdict["entry"],
                "exit":sdict["exit"]}
        cluster_export["Last State"] = {
            "longitude":sf.longitude,
            "name":sf.name,
            "ti":sf.init_time,
            "tf":sf.end_time,
            "slots":state_slots,
            "satnums":sf.satnums,
            "initialized":sf.initialized,
            "active":sf.active}
        cluster_export["Satellites"] = self.get_all_sats()
        cluster_slots = {}
        for slot in self.slots:
            cluster_slots[slot["satnum"]] = {
                "timeframe":[str(t) for t in slot["timeframe"]],
                "entry":slot["entry"],
                "exit":slot["exit"]}
        cluster_export["Slots"] = cluster_slots
        cluster_export["Name"] = self.names[-1]
        event_timeline = {}
        if self.states[0].init_time is None:
            text = f"existing cluster @{self.names[0]} {self.states[0].satnums}"
            event_timeline[str(self.first_active)[:19]] = text
        for event in self.events:
            if event["satnum"] is not None:
                text = [event["satnum"],event["type"],"cluster @"+event["@"],str(event['recipients'])]
            elif event["type"] == "renamed":
                text = ["cluster @"+event["@"][0],event["type"],event["@"][1],str(event['recipients'])]
            else:
                text = ["cluster",event["type"],"@"+event["@"],str(event['recipients'])]
            event_timeline[str(event["timestamp"])[:19]] = ' '.join(text)
        if sf.end_time is None:
            text = f"{[s for s in sf.satnums]} last seen in cluster @{sf.get_name()}"
            event_timeline[str(self.last_seen)[:19]] = text
        cluster_export["Events"] = event_timeline
        return cluster_export

