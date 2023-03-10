# MIT ARCLab GEO Toolbox 🌎 🧰
Here you'll find scripts for GEO-based astrodynamics research projects.

**Contributors:** [Thomas G. Roberts](https://github.mit.edu/thomasgr) and [Liz Solera](https://github.mit.edu/hsolera).

## Required modules
Install the newest versions of these modules to make sure you can run the scripts in this repository.

### Python

#### [csv](https://docs.python.org/3/library/csv.html)
Reading and writing CSV files
#### [datetime](https://pypi.org/project/DateTime/)
Reading and writing various date formats
#### [matplotlib](https://matplotlib.org/)
Making charts, converting date formats
#### [numpy](https://pypi.org/project/numpy/)
Math, mostly
#### [pyephem](https://rhodesmill.org/pyephem/)
Orbit propagation, conversion from orbital elements to geographic coordinates
#### [spacetrack](https://pypi.org/project/spacetrack/)
Interacting with the Space-Track.org API
#### [time](https://docs.python.org/3/library/time.html)
Injecting pauses to not trip up the Space-Track.org pull limiter

## Local file organization
To use any of the scripts in this repository, just save them to a ``Code`` folder within your working directory, organized as follows:

```
📁 .
├── 📁 Data 
│   ├── 📁 TLEs
│   ├── 📁 OEs and LLAs
│   └── 📝 satcats.csv      # List of NORAD IDs / Satellite Catalog IDs ("satcats") for study
└── 📁 Code 
```

## Scripts
A list of the scripts in this directory and what they do. To execute a script, navigate to the ``Code`` directory and run it using either ``python [script].py`` or  ``python3 [script].py``, as directed.

### downloadTLEs.py
Downloads the TLEs associated with each of the satellites in ``satcats.csv``.

**Inputs:** Space-Track.org login credentials, ``satcats.csv``, study period start date ("yyyy-mm-dd"), study period end date ("yyyy-mm-dd").<br>
**Outputs:** One text file per satellite, saved as ``./Data/TLEs/[satcat].txt``.

### dms2decimal.py
Helper script to convert angles measured in degrees, minutes, seconds to decimal degrees. 

### TLEs2OEsandLLAs.py
Converts the downloaded TLEs into orbital elements (OEs) and geographic coordinates (latitutdes, longitudes, and altitudes; LLAs) at specified time steps. At each time step, the script identifies the TLE with the closest epoch to that particular time step, propagates it forwards or backwards in time, the converts the encoded information into OEs and LLAs. If the nearest TLE is more than two weeks away, no OEs and LLAs are printed (as propagating a TLE that far is generally ill-advised.) 

**Inputs:** study period start date ("yyyy-mm-dd"), study period end date ("yyyy-mm-dd"), time step (days).<br>
**Outputs:** One CSV file per satellite, saved as ``./Data/OEs and LLAs/[satcat].csv``, with the following columns: "Time step", "TLE epoch", "Eccentricity", "Semimajor axis (m)", "Inclination (deg)", "RAAN (deg)", "Argument of periapsis (deg)", "Mean anomaly (deg)", "True anomaly (deg)", "Latitude (deg)", "Longitude (deg)", "Altitude (m)".

### histories.py -> history(satcat:int, t1:datetime, t2:datetime)
Defines a class of history objects.

#### Methods
**__init__(satcat:int, t1:datetime, t2:datetime):** Creates a history object associated with a particular satellite. [**Inputs:** satcat id (integer), first timestamp (datetime object), last timestamp (datetime object)]

**OE_LLA():** Associates the historical orbital elements and geographic coordinates in ``./Data/OEs and LLAs/[satcat].csv`` with the history object (file must already exist). Referenced by other class methods and does not need to be called explicitly.

**OE(t1:datetime = None, t2:datetime = None):** Returns an array of timestamps and associated orbital elements over the specified time range. If no time range is specified, it defaults to the pre-specified object date range. [**(Optional)Inputs:** first timestamp (datetime object), last timestamp (datetime object); **Outputs:** 2D numpy array with the following rows: Timestamp (datetime), Eccentricity, Semimajor axis (m), Inclination (deg), RAAN (deg), Argument of periapsis (deg), Mean anomaly (deg), True anomaly (deg)]

**LLA(t1:datetime = None, t2:datetime = None):** Returns an array of timestamps and associated geographic coordinates over the specified time range. If no time range is specified, it defaults to the pre-specified object date range. [**(Optional)Inputs:** first timestamp (datetime object), last timestamp (datetime object); **Outputs:** 2D numpy array with the following rows: Timestamp (datetime), Longitude (deg), Latitude (deg), Altitude (m)]

**CleanLLA(t1:datetime = None, t2:datetime = None):** Returns an array of timestamps and associated, **continuous** geographic coordinates over the specified time range. If no time range is specified, it defaults to the pre-specified object date range.[**(Optional)Inputs:** first timestamp (datetime object), last timestamp (datetime object); **Outputs:** 2D numpy array with the following rows: Timestamp (datetime), Longitude (deg), Latitude (deg), Altitude (m)]

**getTLEepochs(start:datetime, end:datetime):** Helper function that returns the TLE epoch timestamps and associated longitudes. [**Inputs:** first timestamp (datetime object), last timestamp (datetime object); **Outputs:** 1D numpy array of TLE timestamps (datetimes), 1D numpy array of longitudes (floats)]

**PlotEpochColors(datetimes, data, t1:datetime = None, t2:datetime = None, title:str = None):** Generates a scatterplot of a data set with markers that are color-coded according to their timestamps' distances (in hours) from or to the nearest TLE epoch. [**Inputs:** array of timestamps to be plotted, array of data points to be plotted; **(Optional)Inputs:** t1: first plotted timestamp (set to trim data before plotting), t2: last plotted timestamp (set to trim data before plotting), title: figure title]

#### Attributes
*history.satcat* {satcat ID number}

*history.firsttime* {first timestamp associated with object TLEs, OEs, and LLAs (specifying *t1* or *start* in a callable does not affect this)}

*history.lasttime* {last timestamp associated with object TLEs, OEs, and LLAs (specifying *t2* or *end* in a callable does not affect this)}

*history.OE_arr* {array of orbital elements over timestamps between *firsttime* and *lasttime* (calling *history.OE()* is more robust)}

*history.LLA_arr* {array of geographics coordinates over timestamps between *firsttime* and *lasttime* (calling *history.LLA()* is more robust)}

*history.CLeanLLA_arr* {array of continuous geographics coordinates over timestamps between *firsttime* and *lasttime* (calling *history.CleanLLA()* is more robust)}

*history.datetimes* {array of datetimes for all timestamps between *firsttime* and *lasttime*}

*history.timestep* {time in seconds between each timestamp from ``./Data/OEs and LLAs/[satcat].csv``}

*history.scEpoch* {array of time difference in hours between each timestamp in *datetimes* and the nearest TLE epoch}

### demo.py
Examples of potential use cases for callables in other GEOToolbox scripts:
- history class & methods
- more coming soon
