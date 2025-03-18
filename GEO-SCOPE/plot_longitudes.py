import numpy as np
from datetime import datetime, timedelta, timezone
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Read in list of strings from csv file
def import_satcats(satcat_file):
    with open(satcat_file, 'r') as f:
        satcats = []
        reader = csv.reader(f, delimiter=",")
        for row in reader: 
            if len(row) > 0: satcats.append(str(row[0]))
    return satcats
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
# Read in numpy array from csv file
def import_longitude(lon_file,t_range=None,expnd=True):
    times = []
    lon = []
    with open(lon_file, encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=",")
        next(reader)
        for row in reader:
            if len(row) > 0:
                if t_range is None: 
                    times.append(datetime.fromisoformat(row[0]))
                    lon.append(float(row[10]))
                elif t_range[0] <= datetime.fromisoformat(row[0]) <= t_range[1]:
                    times.append(datetime.fromisoformat(row[0]))
                    lon.append(float(row[10])) # (-180,180)
    lon360 = np.array(lon)
    for i in range(1,len(lon)):
        l0 = lon360[i-1]
        l1 = lon360[i]
        ld = l0 - l1
        if np.abs(lon360[i-1]-lon360[i])>180:
            s = -1 if ld < 0 else 1
            n = 180 if np.abs(l1) <= 180 else 360
            lon360[i] = l1 + (n*(int(ld/n)+s))
    if expnd: return np.vstack([np.array(times), lon360])
    else: return np.vstack([np.array(times), np.array(lon)])
# Create a list of all longitude arrays for each satellite in satcats
def read_longitudes(data_folder, satcats, t_range=None, expnd=True):
    longitudes = {}
    for satcat in satcats:
        longitudes[satcat] = import_longitude(data_folder + satcat + '.csv', t_range, expnd)
    return longitudes
# Plot all longitudes in longitudes
def plot_longitudes(lons, save_path=None, fig_title=None, t_range=None, lon_range=None, nodes=None, ncolors=None):
    # Create the plot
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['mathtext.fontset'] = 'stix'
    plt.rcParams['font.family'] = 'STIXGeneral'
    plt.rcParams['font.size'] = 8
    fig, ax = plt.subplots()
    fig.set_figheight(5)
    fig.set_figwidth(10)
    for satcat, data in lons.items():
            plt.plot(data[0][:], data[1][:], label=satcat,linewidth=0.5)
    if (nodes is not None) and (ncolors is not None):
        for vline, color in zip(nodes, ncolors):
            plt.axvline(x=vline, color=color, linestyle='--')
    elif nodes is not None:
        for vline in nodes:
                plt.axvline(x=vline, color='r', linestyle='--')
    # Add title and labels
    ax.set_ylabel('Longitude (deg)')
    locator = mdates.AutoDateLocator(minticks=5, maxticks=15)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    if t_range is not None:
        ax.set_xlim(t_range)
    if lon_range is not None:
        ax.set_ylim(lon_range)
    # Add legend
    ax.legend()
    # Show the plot
    if save_path is not None and fig_title is not None:
        plt.savefig(save_path+fig_title+".png")
        plt.close()
    else: plt.show()
def plot_londr(sat0, save_path=None, fig_title=None, t_range=None, lon_range=None, drp_range=None, drm_range=None, nodes=None, ncolors=None, plot_alt=False):
    # Create the plot
    # plt.rcParams['figure.dpi'] = 300
    plt.rcParams['mathtext.fontset'] = 'stix'
    plt.rcParams['font.family'] = 'STIXGeneral'
    # plt.rcParams['font.size'] = 8
    fig, ax = plt.subplots(3,1) if not plot_alt else plt.subplots(4,1)
    fig.set_figheight(2)
    fig.set_figwidth(4)
    for satcat, data in sat0.items():
        ax[0].plot(data[0][:], data[1][:], label=satcat,linewidth=0.5)
        ax[1].plot(data[0][:], data[2][:], label='drp',linewidth=0.5)
        ax[2].plot(data[0][:], data[3][:], label='drm',linewidth=0.5)
        if plot_alt: ax[3].plot(data[0][:], data[4][:], label='alt',linewidth=0.5)
        drp_range = [0.0,0.02] if np.max(data[2][:]) > 2.0 else None
        drm_range = [0.0,0.005] if np.max(data[3][:]) > 1.0 else None
    if plot_alt:
        ax[3].axhline(y=35786000, color='g', linestyle='--')
        ax[3].axhline(y=36086000, color='r', linestyle='--')
    if nodes is not None and ncolors is not None:
        for vline, color in zip(nodes, ncolors):
            ax[0].axvline(x=vline, color=color, linestyle='--')
            ax[1].axvline(x=vline, color=color, linestyle='--')
            ax[2].axvline(x=vline, color=color, linestyle='--')
            if plot_alt: ax[3].axvline(x=vline, color=color, linestyle='--')
    # Add title and labels
    ax[0].set_ylabel('Longitude (deg)')
    ax[1].set_ylabel('DR Phase (deg/day)')
    ax[2].set_ylabel('DR Mean (deg/day)')
    if plot_alt: ax[3].set_ylabel('Altitude (m)')

    locator = mdates.AutoDateLocator(minticks=5, maxticks=15)
    formatter = mdates.ConciseDateFormatter(locator)
    ax[0].xaxis.set_ticklabels([])
    ax[1].xaxis.set_ticklabels([])
    if plot_alt:
        ax[2].xaxis.set_ticklabels([])
        ax[3].xaxis.set_major_locator(locator)
        ax[3].xaxis.set_major_formatter(formatter)
    else:
        ax[2].xaxis.set_major_locator(locator)
        ax[2].xaxis.set_major_formatter(formatter)
    if t_range is not None:
        ax[0].set_xlim(t_range)
        ax[1].set_xlim(t_range)
        ax[2].set_xlim(t_range)
        if plot_alt: ax[3].set_xlim(t_range)
    if lon_range is not None:
        ax[0].set_ylim(lon_range)
    if drp_range is not None:
        ax[1].set_ylim(drp_range)
    if drm_range is not None:
        ax[2].set_ylim(drm_range)
    # Add legend
    ax[0].legend()
    # Show the plot
    if save_path is not None and fig_title is not None:
        plt.savefig(save_path+fig_title+".png")
    else: plt.show()
