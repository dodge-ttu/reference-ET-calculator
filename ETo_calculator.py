from datetime import datetime
from matplotlib import pyplot as plt
import pandas as pd
import math
import numpy as np
from scipy import stats

DF = pd.read_csv("https://drive.google.com/uc?id=1K7vnCpK8tElmE-VfyMiN4pQSQEAkOrTE") # bushland data set W. Guo Spring 2018

def put_colon_in_time(pandas_series):
    """ Convert the data in the raw weather data set to a string and insert a colon in correct place.
    
    :param pandas_series: pandas series of time without a colon, ex. "115" rather than "01:15"
    """
    
    time_as_string = [str(i) for i in pandas_series]
    fixed_time = []
    for i in time_as_string: # place colon in time columns so time parser understands
        if len(i) == 0:
            pass
        elif len(i) == 1:
            tm = "00:0" + i
        elif len(i) == 2:
            tm = "00:" + i
        elif len(i) == 3:
            tm = "0" + i[0] + ":" + i[1] + i[2]
        else:
            tm = i[0] + i[1] + ":" + i[2] + i[3]
        fixed_time.append(tm)
    return fixed_time

# Run function and fix time column
DF["TimeWcolon"] = put_colon_in_time(DF["Time"])

def change_24(time_with_colon):
    """ Change the times in the data that are 24:00 to 23:59 because we are scaling this data to a dialy time step and this change           becomes inconsequential in the ETo estimation.
    
    :param time_with_colon: a pandas series of strings representing HH:MM containing 24:00 values
    """
    
    TimeNo24 = []
    for i in time_with_colon:
        if i == "24:00":
            i = "23:59"
        else:
            i = i
        TimeNo24.append(i)
    
    return TimeNo24
    
# Run function and remove 24:00
DF["TimeNo24"] = change_24(DF["TimeWColon"])

# Combine the 'year', 'DOY, and 'TimeNo24' into parsable string
DF["date"] = DF["Year"].map(str)+"-"+DF['DOY'].map(str)+" "+ DF["TimeNo24"].map(str) 

# Parse date and time
DF["date"] = pd.to_datetime(DF["date"], format = "%Y-%j %H:%M")

# Set "date" column to index
DF = DF.set_index(DF["date"])

# Drop intermediate time columns no longer needed
DF = DF.drop(columns=["date","TimeWcolon","TimeNo24"])

# Remove error values
DF["AirTemp"] = DF["AirTemp"][(DF["AirTemp"] < 45) & (DF["AirTemp"] > -30)]
DF["RelHumid"] = DF["RelHumid"][(DF["RelHumid"] < 100) & (DF["RelHumid"] > 0)]
DF["SolRad"] = DF["SolRad"][(DF["SolRad"] < 2000) & (DF["SolRad"] > 0)]
DF["WS_2m"] = DF["WS_2m"][(DF["WS_2m"] < 18) & (DF["WS_2m"] > 0)]
DF["BP"] = DF["BP"][(DF["BP"] < 120) & (DF["BP"] > 0)]
DF["Rainfall_Tot"] = DF["Rainfall_Tot"][(DF["Rainfall_Tot"] < 200) & (DF["Rainfall_Tot"] > 0)]

# If test returns True  missing values exist in given series
DF["AirTemp"].isnull().values.any()

# Interpolate missing values
DF["AirTemp"] = DF["AirTemp"].interpolate()
DF["RelHumid"] = DF["RelHumid"].interpolate()
DF["SolRad"] = DF["SolRad"].interpolate()
DF["WS_2m"] = DF["WS_2m"].interpolate()
DF["BP"] = DF["BP"].interpolate()

# Don't interpolate rainfall, just replace missing values with 0
DF["Rainfall_Tot"] = DF["Rainfall_Tot"].fillna(0)

# Create a daily data set from our clean 15 minute data
DF_daily = DF.resample('24H').mean()

# Extract required dialy min and max value with groupby()
DF_daily["mint.C"] = DF.groupby('DOY').min()["AirTemp"].values
DF_daily["maxt.C"] = DF.groupby('DOY').max()["AirTemp"].values
DF_daily["min.RH.%"] = DF.groupby('DOY').min()["RelHumid"].values
DF_daily["max.RH.%"] = DF.groupby('DOY').max()["RelHumid"].values

# Use sum() for rain rather that mean() when aggregation to larger time step
DF_daily["Rain_Tot"] = DF.loc[:,("Rainfall_Tot")].resample('24H').sum()

# Rename and organize data
new_names = {"year":DF_daily["Year"],
               "day":DF_daily["DOY"],
               "radn.W/m2":DF_daily["SolRad"],
               "wind.2m.m/s":DF_daily["WS_2m"],
               "bar.press.kPa":DF_daily["BP"],
               "mint.C":DF_daily["mint.C"],
               "maxt.C":DF_daily["maxt.C"],               
               "min.RH.%":DF_daily["min.RH.%"],
               "max.RH.%":DF_daily["max.RH.%"],
               "rain.mm":DF_daily["Rain_Tot"]} 

DF = pd.DataFrame(new_names)

# Mean dail temp
DF["avgt.C"] = (DF["mint.C"] + DF["maxt.C"]) / 2

# Display a few lines of solar radiation values
DF["radn.W/m2"][:5] # W m^-2

# Convert solar radiation
DF["radn.MJ/m2"] = DF["radn.W/m2"] * 0.0864

# Display a few lines of solar values
DF["wind.2m.m/s"][:5]

# check max wind speed value
max_wind_avg_2m = (max(DF["wind.2m.m/s"]) / 1609.34) * 3600
max_wind_avg_2m 

# Slope of saturation vapor pressure
DF["delta"] = 4098 * (0.6106 * np.exp((17.27 * DF["avgt.C"])/(DF["avgt.C"] + 237.3))) / ((DF["avgt.C"] + 237.3)**2)

# Atmospheric pressure
elevation = 992 # high plains of texas
P = 101.3 * (((293 - (0.0065 * elevation)) / 293) ** 5.26)

# Psychrometric constant
gamma = 0.000665 * P

# Delta Term
DF["delta.term"] = DF["delta"] / (DF["delta"] + (gamma * (1 + 0.34 * DF["wind.2m.m/s"])))

# Psi Term
DF["psi.term"] = gamma / (DF["delta"] + (gamma * (1 + 0.34 * DF["wind.2m.m/s"])))

# Temperature Term
DF["temp.term"] = (900 / (DF["avgt.C"] + 273)) * DF["wind.2m.m/s"]

# Mean saturation vapor pressure
DF["max.sat.vap"] = 0.6108 * np.exp((17.27 * DF["maxt.C"]) / (DF["maxt.C"] + 237.3))
DF["min.sat.vap"] = 0.6108 * np.exp((17.27 * DF["mint.C"]) / (DF["mint.C"] + 237.3))
DF["mean.sat.vap"] = (DF["min.sat.vap"] + DF["max.sat.vap"]) / 2

# Actual vapor pressure
DF["actual.vap"] = ((DF["min.sat.vap"] * (DF["max.RH.%"] / 100)) + (DF["max.sat.vap"] * (DF["min.RH.%"] / 100))) / 2

# Solar dec / inverse sun
DF["earth.sun.rel.dis"] = 1 + (0.033 * np.cos(((2 * math.pi)/365) * DF["day"]))
DF["solar.decl"] = 0.409 * np.sin((((2 * math.pi)/365) * DF["day"]) - 1.39)

# latitude in radians
lat_in_rad = (math.pi / 180) * (35.1905)

# Sunset hour angle
DF["sunset_angle"] = np.arccos(-math.tan(lat_in_rad) * np.tan(DF["solar.decl"]))

# Extraterestrial Rad
aa = DF["sunset_angle"]*np.sin(lat_in_rad)*np.sin(DF["solar.decl"])
bb = np.cos(lat_in_rad)*np.cos(DF["solar.decl"])*np.sin(DF["sunset_angle"])

DF["extraT_rad"] = (((24*60)/math.pi)*0.0820*DF["earth.sun.rel.dis"])*(aa + bb)

# Clear sky rad
DF["clr_sky_rad"] = (0.75 + (2e-5)*elevation) * DF["extraT_rad"]

# Net short rad
albedo = 0.23
DF["net.rad.MJ/m2*day"] = (1 - 0.23) * DF["radn.MJ/m2"]

# Net long rad out
sb_const = 4.903e-9
DF["sb_flux"] = ((DF["maxt.C"]+273.16)**4 + (DF["mint.C"]+273.16)**4)/2
DF["outLW_rad"] = sb_const * (DF["sb_flux"] * (0.34-(0.14*np.sqrt(DF["actual.vap"])))*(1.35*(DF["radn.MJ/m2"]/DF["clr_sky_rad"]) - 0.35))

# Net rad
DF["total.net.rad"] = DF["net.rad.MJ/m2*day"] - DF["outLW_rad"]

# Net rad in mm of water
DF["total.net.rad.mm"] = DF["total.net.rad"] * 0.408

# Overall equation -- ET_rad
DF["ET_rad"] = DF["delta.term"] * DF["total.net.rad.mm"]

# Overall equation -- ET_wind
DF["ET_wind"] = DF["psi.term"]*DF["temp.term"]*(DF["mean.sat.vap"] - DF["actual.vap"])

# Final ref ET
DF["ETo"] = DF["ET_rad"] + DF["ET_wind"]

# Plot data
d = {"ETo":DF["ETo"],"total.net.rad":DF["total.net.rad"],"wind.2m.m/s":DF["wind.2m.m/s"]}
data = pd.DataFrame(d)
cols_data = list(data)
plt.figure(figsize=(22,8))

for i in cols_data:
    if i == "ETo":
        plt.plot(data[i], "o")
    elif i == "total.net.rad":
        plt.plot(data[i], "-.")
    else:
        plt.plot(data[i])
    print("Plotting: " + str(i))
    
plt.legend(prop={'size':12})


















