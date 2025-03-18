class drive:
    def __init__(self,home,ephems,satcats,clusters,slots,save4later,plots):
        self.home = home
        self.ephems = ephems
        self.satcats = satcats
        self.clusters = clusters
        self.slots = slots
        self.save4later = save4later
        self.plots = plots                 
                 
    def new_directory(self, name, value):
        setattr(self, name, value) 
        
    def new_directories(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)



import os
Current_Directory = os.path.dirname(os.path.realpath(__file__))+"/" # Should work across linux/windows/mac & python 3.6+

myDirectories = drive(
                    home = Current_Directory,
                    ephems = Current_Directory + "LLAs/",
                    satcats = Current_Directory + "satcats/geosats.csv",
                    clusters = Current_Directory + "TLE Results/cluster_histories.yaml",
                    slots = Current_Directory + "TLE Results/satellite_histories.yaml",
                    save4later = Current_Directory + "TLE Results/last_cluster_status.yaml",
                    plots = Current_Directory + "Plots/TLE Clusters/"
                    )
