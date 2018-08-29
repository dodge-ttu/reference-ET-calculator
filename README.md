# ETo via FAO-56 and Python
### A guide for calculating reference evapotranspiration in Python with a sample data set
<img src="https://drive.google.com/uc?id=1TLUYQ7uSpISZI2V3CVF15XrhhiJPENj1">

#### Will Dodge Spring 2018

<br></br>

---

<br></br>

### Overview

Evapotranspiration (ET) is a term used in agriculture to describe total evaporation from soil and plant surfaces over time. This value is estimated from four basic climate parameters: solar radiation, air temp, wind speed, and relative humidity. Understanding how much water is leaving an agricultural system on a daily basis is fundamental to efficient crop management. The development of a reasonable ET model began more than a century ago and continues today. The Food and Agriculture Organization of the United Nations has developed a method for calculating evapotranspiration (ET) as well as the more useful reference evapotranspiration (ETo). The official name of the ETo model supported by the united nations is <a href="http://www.fao.org/docrep/X0490E/X0490E00.htmFAO-56">FAO-56</a>.

In February of 2010 the researchers at the University of Florida Institute of Food and Agricultural Sciences published a 
<a href="https://drive.google.com/file/d/1EVjUARYY0g5o0ioVy70yANynh8DAQ4ir/view?usp=sharing">beautiful paper</a> detailing a step by step method for calculating ETo based on the FAO-56 model. The crux of the model is the requirement for clean climate data for the four key parameters. Weather data is widely available but not always complete or in units appropriate for FAO-56. Python is a powerful programming language with superior data wrangling capacity. Here we leverage the power of Python to clean and organize daily climate data, calculate ETo, and build widgets suitable for use in a <a href="jupyter.org">Jupyter Notebook</a>.

<br></br>

---

<br></br>

### Observation data required

The required parameters for calculating ET<sub>o</sub> are solar radiation, wind speed, air temperature, and relative humididity. The specifics of these observations is well documented in the publication this model is based upon. In the event that one is missing data or entire parameters the official documentation at the <a href="http://www.fao.org/docrep/X0490E/x0490e00.htm#Contents">FAO website</a> sould be consulted to determine the approach to calculating ETO without said missing variable. In this guide a link is provided so that users can read a test csv from URL meaning tha one does not need a weather data set of their own to work through this tutorial.

### The chart below describes the weather data required

<img src="https://drive.google.com/uc?id=1scDh_GzljhJ6AyVDlQz-k_ZadNvyW6Sc">

### Import required libraries

```
from datetime import datetime
from matplotlib import pyplot as plt
import pandas as pd
import math
import numpy as np
from scipy import stats
````
### Read weather data into Pandas data frame

In this script the raw <code>.csv</code> data is coming from a google drive shareable link. This is <b>great</b> because the notebook itself can be distributed without needing to also distrubute a slew of assocaited file data. The other thing is that <b>users who execute this code will not have to adjust the filepath given</b> to the <code>pd.read_csv()</code> command.

```
DF = pd.read_csv("https://drive.google.com/uc?id=1K7vnCpK8tElmE-VfyMiN4pQSQEAkOrTE")
```

<br></br>

---

<br></br>

## The test data needs to be cleaned

In the test data set included in this tutorial has some issues. Most large weather data sets will have some sort of cleaning that needs to be done. This may be interpoloating missing values, changing time resolution, or removing known bad values like -9999. In the case of this test data we have several issues. There are missing values, the time is missing a colon to separate the minutes from the seconds, the time step is 15 minutes and we need daily time series data, the units are not correct, and there are known bad values. 

### Let's begin by fixing the time

```
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
```

### Python only understands 00-23 hour days

Python only reads datetime with hours <code>00:00 - 23:59 (HH:MM - HH:MM)</code>, for example <code>23:15</code> is fine for 23rd hour and 15th minute. Our data contains <code>24:00</code> which will not work so <b>one option</b> is to change <code>24:00</code> to <code>23:39</code>. This is appropriate in this case becuse we are scailing the data up with regard to the time step as well as beacuse our date begins at zero and ends at the 23rd hour. Now the datetime parser will be able to covert our dates, which are strings, into a propper datetime series. If we wanted, we could change the time to <code>23:59:59 (HH:MM:SS)</code> so that we would only be altering the series by a single second. That is not necessary here because we are scaling to a daily time step.

```
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
```

### Concantonate date and time strings for parsing

Up to this point our date and time have been in the form of strings. We want to concantonate the <code>Year</code>, <code>DOY</code>, and <code>TimeNo24</code> into a single string that we can parse. The individual components of the datetime are in the proper fromat and will parse nicely. The only thing to recognize is that our date is a <b>julian date</b>. This is the same as <i>day of year</i>. To be sure that the parser is efficient, We pass the argument <code>format = "%Y-%j %H:%M"</code> to the parser.

```
# Combine the 'year', 'DOY, and 'TimeNo24' into parsable string
DF["date"] = DF["Year"].map(str)+"-"+DF['DOY'].map(str)+" "+ DF["TimeNo24"].map(str) 

# Parse date and time
DF["date"] = pd.to_datetime(DF["date"], format = "%Y-%j %H:%M")
```

### Set clean datetime column to time series index

If we set the index of the data frame to the datetime series, then creating subsets and data visualtions becomes simplified. A datetme index will preserve the chronological order of our data at all times.

```
# Set "date" column to index
DF = DF.set_index(DF["date"])

# Drop intermediate time columns no longer needed
DF = DF.drop(columns=["date","TimeWcolon","TimeNo24"])
```

### Remove exremely high and low values from data

In our raw data there are extremely high and low values which are errors that have occured with a sensor during the logging period. We know what reasonable values are for our weather parameters so we can set up a filter for each variable in our data frame. If we find that a value is extremely high or low we can replace the value with the mean for the variable. We could also remove the value and then interpolate but for simplicity im just going to replace bad values with the varaible mean.

```
# Remove error values

DF["AirTemp"] = DF["AirTemp"][(DF["AirTemp"] < 45) & (DF["AirTemp"] > -30)]
DF["RelHumid"] = DF["RelHumid"][(DF["RelHumid"] < 100) & (DF["RelHumid"] > 0)]
DF["SolRad"] = DF["SolRad"][(DF["SolRad"] < 2000) & (DF["SolRad"] > 0)]
DF["WS_2m"] = DF["WS_2m"][(DF["WS_2m"] < 18) & (DF["WS_2m"] > 0)]
DF["BP"] = DF["BP"][(DF["BP"] < 120) & (DF["BP"] > 0)]
DF["Rainfall_Tot"] = DF["Rainfall_Tot"][(DF["Rainfall_Tot"] < 200) & (DF["Rainfall_Tot"] > 0)]
```

### Interpolate missing values

Now that we have eliminated numerical values that are either impossible or extremly unlikely, we still need to get rid of missing values. There appears to be more than a few in our original fifteen minute set but we can easily correct this with <code>DF.interpolate()</code>.

```
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

```

### Extract daily highs and lows

For several of our parameters we need a daily high and low. We are going to use <code>DF.resample()</code> to scale our time resolution up, but we also need to extract a daily high and low value for temperature and relative humidity. The minimum and maximun values will be used in later calculations.

```
# Create a daily data set from our clean 15 minute data
DF_daily = DF.resample('24H').mean()

# Extract required dialy min and max value with groupby()
DF_daily["mint.C"] = DF.groupby('DOY').min()["AirTemp"].values
DF_daily["maxt.C"] = DF.groupby('DOY').max()["AirTemp"].values
DF_daily["min.RH.%"] = DF.groupby('DOY').min()["RelHumid"].values
DF_daily["max.RH.%"] = DF.groupby('DOY').max()["RelHumid"].values

# Use sum() for rain rather that mean() when aggregation to larger time step
DF_daily["Rain_Tot"] = DF.loc[:,("Rainfall_Tot")].resample('24H').sum()
```

### Rename and reorder columns

```
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
```

Our data is now clean, organized, and ready for ETo calculation!

<br></br>

--- 

<br></br>

## Step by Step ETo Calculation

### Calculate daily mean temperature, ℃

We need the daily temperature average. We caclulate this from the daily min and max temperature values from the raw data. I have included a line at the end of each step to show the output of our calculations. This is important so that we can monitor the output as we go and hopefully identify the source of any possible errors. 

```
DF["avgt.C"] = (DF["mint.C"] + DF["maxt.C"]) / 2
```

### Calculate mean daily solar radiation (R<sub>s</sub>), MJ m<sup>-2</sup> day<sup>-1</sup>

This variable is calculated in our raw weather data but in different units than we require. So we need a conversion because the values for solar radiation are in W/m<sup>2</sup>.

```
# Display a few lines of solar radiation values
DF["radn.W/m2"][:5] # W m^-2
```

### Convert daily solar from watts to megajoules, MJ m<sup>-2</sup> day<sup>-1</sup>

Here we make a conversion from W/m<sup>2</sup> to MJ m<sup>-2</sup> day<sup>-1</sup> by multiplying our observed solar by 0.0864.

```
# Convert solar radiation
DF["radn.MJ/m2"] = DF["radn.W/m2"] * 0.0864
```

### The average daily wind speed (<i><b>u</b></i><sub>2</sub>), m s<sup>-1</sub>

Measured two meters above a realatively flat surface. This in an observed value in our raw data already in correct units, <b>meters per second</b>.

```
# Display a few lines of solar values
DF["wind.2m.m/s"][:5]
```

### Convert max wind averge to <i>miles per hour</i> to check data

Our value is in meters per second but we can convert this to miles per hour. Divide the by <b>1609.34 meters to convert meters to miles</b> and then <b>multiply by 3600 seconds</b> to convert seconds to hours.

```
# check max wind speed value
max_wind_avg_2m = (max(DF["wind.2m.m/s"]) / 1609.34) * 3600
max_wind_avg_2m 
```

### Slope of the saturation vapor pressure curve (Delta), kPa

<br></br>

<img src="https://drive.google.com/uc?id=1uA6Zo-K6dcbzuBiNDWyU_K61Tvd6pmH7">

<br></br>

```
DF["delta"] = 4098 * (0.6106 * np.exp((17.27 * DF["avgt.C"])/(DF["avgt.C"] + 237.3))) / ((DF["avgt.C"] + 237.3)**2)
```

### Atmospheric Pressure (P), kPa 

This is the pressure exerted by the weight of the earth's atmosphere. Altitude is factor when calculating this varaible. This model uses the equation in the following figure. We will make the calculation once in this model and use that as a contstant atmospheric pressure for this altitude. In the following equation <b>Z is altitude in meters</b>.

<br></br>

<img src="https://drive.google.com/uc?id=1pIpkTvzi88OcoCTiPHRPq7_Xu5lEX6dm">

<br></br>

```
elevation = 992 # high plains of texas

P = 101.3 * (((293 - (0.0065 * elevation)) / 293) ** 5.26)
```

### Psychrometric constant (gamma), kPa ℃<sup>-1</sup>

This variable is the relationsip between the partial pressure of water vapor in the air and temperature. It uses our calculated atmospheric pressure (P) value to estimate the psychrometric constant. This value will be used to calculate saturated vapor pressure.

<br></br>

<img src="https://drive.google.com/uc?id=1tBdICICKsNEwZg5GaYGTioVlA3a2aM2v">

<br></br>

```
gamma = 0.000665 * P
```

### Delta Term (DT), auxiliary calculation for the radiation term

To simplify the overall ET<sub>o</sub> we can calculate portions of the equation seperately. The Delta Term will be used to calculate our radiation driven ET<sub>o</sub> terms in later steps.

<br></br>

<img src="https://drive.google.com/uc?id=1vxH1NEzFgqZx81b4AJOwbz8ym0OtOFF6">

<br></br>

```
DF["delta.term"] = DF["delta"] / (DF["delta"] + (gamma * (1 + 0.34 * DF["wind.2m.m/s"])))
```

### Psi Term (PT), auxiliary calculation for the wind term

Again, we make an auxiliary calculation to simplify the overall ET<sub>o</sub> process. The Psi Term will be used to calculate our wind driven ET<sub>o</sub> terms in later steps.

<br></br>

<img src="https://drive.google.com/uc?id=1yVSXpAr2bQOrUbF9vPwkcsRP3RI_jNav">

<br></br>

```
DF["psi.term"] = gamma / (DF["delta"] + (gamma * (1 + 0.34 * DF["wind.2m.m/s"])))
```

### Temperature Term (TT), auxiliary calculation for the wind term

Again, we make an auxiliary calculation to simplify the overall ET<sub>o</sub> process. The Temperature Term will be used to calculate our wind driven ET<sub>o</sub> terms in later steps. This term incorperates the average daily temperature while the previous two auxiliary terms did not. 

<br></br>

<img src="https://drive.google.com/uc?id=1000hFVfIePFDMbEvi4BEkoM6GS8gSvVO">

<br></br>

```
DF["temp.term"] = (900 / (DF["avgt.C"] + 273)) * DF["wind.2m.m/s"]
```

### Calculate mean saturation vapor pressure (e<sub>s</sub>), kPa

Saturated vapor pressure is a fucntion of temperature and therefore can be calculated with air temperature. The following equation describes the relationship between temperature and saturated vapor pressure. <b>Temperature (T) is in degrees celcius</b>.

<br></br>

<img src="https://drive.google.com/uc?id=12WEdLnr77AXwSWv-2_Ru7NjBRzPdv-91">

<br></br>

The approach will be to calculate a minimum and maximum daily saturated vapor pressure value and use those to calculate the daily mean value. We will use the following equations to calculate the minimums and maximums.

<br></br>

<img src="https://drive.google.com/uc?id=1LkqbHD6iqmhR9rpOsd3XUnOfhNjW5fs3">

<br></br>

```
DF["max.sat.vap"] = 0.6108 * np.exp((17.27 * DF["maxt.C"]) / (DF["maxt.C"] + 237.3))
DF["min.sat.vap"] = 0.6108 * np.exp((17.27 * DF["mint.C"]) / (DF["mint.C"] + 237.3))
DF["mean.sat.vap"] = (DF["min.sat.vap"] + DF["max.sat.vap"]) / 2
```

### Actual vapor pressure (e<sub>a</sub>) derived from relative humidity, kPa

<br></br>

<img src="https://drive.google.com/uc?id=1l4_ZN1HjjDA4Lj1Oa09MyxPOWhqcC-Ch">

<br></br>

```
DF["actual.vap"] = ((DF["min.sat.vap"] * (DF["max.RH.%"] / 100)) + (DF["max.sat.vap"] * (DF["min.RH.%"] / 100))) / 2
```

### Inverse relative Earth-Sun distance (<i><b>d</b></i><sub>r</sub>) and solar declination (δ) 

We calculate these values so that we can estimate extraterrestrial radiation in the next equation. In the following equation <b><i>J</i> is the julian day or day of year</b> ranging from 1-365 on a non leap year.

<br></br>

<img src="https://drive.google.com/uc?id=1aPFBE1HI3ZqIxzWC8CzzIPdLOa8kLUHA">

<br></br>

```
DF["earth.sun.rel.dis"] = 1 + (0.033 * np.cos(((2 * math.pi)/365) * DF["day"]))
DF["solar.decl"] = 0.409 * np.sin((((2 * math.pi)/365) * DF["day"]) - 1.39)
```

### Conversion of latitude (<i><b>φ</b></i>) in degrees to radians

Now we will begin a series of calculations required to calculate the incoming exraterrestrial radian. This will ultimately allow us to calculate a value for net radation from all sources in later steps. <b>Be sure to change the latitude value to the location data was collected.</b>

<br></br>

<img src="https://drive.google.com/uc?id=1RIMx9JbdKT9IdUkbRpskh1b1bHdudQji">

<br></br>

```
lat_in_rad = (math.pi / 180) * (35.1905)
```

### Sunset hour angle (<b><i>ω<sub>s</sub></i></b>)

Again, this calculation will be used in our estimation of extraterrestrial radiation.

<br></br>

<img src="https://drive.google.com/uc?id=1MqQgOs5djIuE97klAeGnjhavrdNyb8rT">

<br></br>

```
DF["sunset_angle"] = np.arccos(-math.tan(lat_in_rad) * np.tan(DF["solar.decl"]))
```

### Extraterrestrial radiation (<b><i>R<sub>a</sub></i></b>), MJ m<sup>-2</sup> day<sup>-1</sup>

This is the extratestrial radiation for each day. This calculation incorperates the previous compnents: <b><i>ω</i></b><sub>s</sub>, 
<b><i>d</i></b><sub>r</sub>, <b><i>φ</i></b>, <b><i>δ</i></b>.

<br></br>

<img src="https://drive.google.com/uc?id=1u__eQbMEQ8fhCNn8vZgE-JkRuMxHfggL">

<br></br>
 
```
aa = DF["sunset_angle"]*np.sin(lat_in_rad)*np.sin(DF["solar.decl"])
bb = np.cos(lat_in_rad)*np.cos(DF["solar.decl"])*np.sin(DF["sunset_angle"])

DF["extraT_rad"] = (((24*60)/math.pi)*0.0820*DF["earth.sun.rel.dis"])*(aa + bb)
```

### Clear sky solar radiation (R<sub>so</sub>), MJ m<sup>-2</sup> day<sup>-1</sup>

The calculation of the clear sky radiation is given by the following equation. <b><i>Z</i></b> the same elevation value we used previously.

<br></br>

<img src="https://drive.google.com/uc?id=1xNO_UtRH95ktX-bMdXTWPvywJDZpOyk1">

<br></br>

```
DF["clr_sky_rad"] = (0.75 + (2e-5)*elevation) * DF["extraT_rad"]
```

### Net solar or net shortwave radiation (R<sub>ns</sub>), MJ m<sup>-2</sup> day<sup>-1</sup>

<br></br>

<img src="https://drive.google.com/uc?id=1FqNN0XwKWUTnJ4DViKKHHVI1qLcKfjdS">

<br></br>

```
albedo = 0.23
DF["net.rad.MJ/m2*day"] = (1 - 0.23) * DF["radn.MJ/m2"]
```

### Net outgoing long wave solar radiation (R<sub>nl</sub>), MJ m<sup>-2</sup> day<sup>-1</sup>

The rate of longwave energy emission is proportional to the absolute temperature of the surface raised to the fourth power. This is expressed in the <i>Stefan-Boltzman Law</i>. The net flux is less than Stefan-Boltzman, however. The abosrption and downward radiation from the sky reduces this enrgy flux.

<br></br>

<img src="https://drive.google.com/uc?id=1ZJSo4jsDwTGhpRqiSt1nraBGkeg7PhmU">

<br></br>

```
sb_const = 4.903e-9
DF["sb_flux"] = ((DF["maxt.C"]+273.16)**4 + (DF["mint.C"]+273.16)**4)/2
DF["outLW_rad"] = sb_const * (DF["sb_flux"] * (0.34-(0.14*np.sqrt(DF["actual.vap"])))*(1.35*(DF["radn.MJ/m2"]/DF["clr_sky_rad"]) - 0.35))
```

### Net radiation (R<sub>n</sub>), MJ m<sup>-2</sup> day<sup>-1</sup>

Net radiation (R<sub>n</sub>) is the difference between the incoming net shortwave radiation (R<sub>ns</sub>) and the outgoing net longwave radiation (R<sub>nl</sub>). We can express this a mega joules and in terms of water.

<br></br>

<img src="https://drive.google.com/uc?id=1__YSiO1vUaCdLM6GD0zaqpeuRwQWR_Bp">

<br></br>

```
DF["total.net.rad"] = DF["net.rad.MJ/m2*day"] - DF["outLW_rad"]
```

We can now convert the net solar radaition into mm of water by multiply our net radiation by a constant that represents the heat of vaporization of water.

<br></br>

<img src="https://drive.google.com/uc?id=1J5olunrf2YdLn5MznHQtOTdFVHBAvxSC">

<br></br>

```
DF["total.net.rad.mm"] = DF["total.net.rad"] * 0.408
```

---

<br></br>

## Overall ET<sub>o</sub> equation

### Final radiation driven ET value, (ET<sub>rad</sub>), mm d<sup>-1</sup>

<br></br>

<img src="https://drive.google.com/uc?id=18GT2SUT_wUz-kf44eD4lCrdWFTDBQCF_">

<br></br>

```
DF["ET_rad"] = DF["delta.term"] * DF["total.net.rad.mm"]
```
### Final wind driven ET value, (ET<sub>wind</sub>), mm d<sup>-1</sup>

<br></br>

<img src="https://drive.google.com/uc?id=1MYEAhfSb0X8wXEO8Ki7Gp5ZyLKkh0A9d">

<br></br>

```
DF["ET_wind"] = DF["psi.term"]*DF["temp.term"]*(DF["mean.sat.vap"] - DF["actual.vap"])
```

### <b>Final Reference Evapotranspiration value, (ET<sub>o</sub>), mm d<sup>-1</sup></b>

<br></br>

<img src="https://drive.google.com/uc?id=1iqqgHvmUCObACrWFP_3Zu6dbBKMe6hXA">

<br></br>

```
DF["ETo"] = DF["ET_rad"] + DF["ET_wind"]
```

<br></br>

---

<br></br>

## Plot ETo data

```
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
```

<br></br>

<img src="https://drive.google.com/uc?id=1ILSZVhyiB1QaqJkI1kTWjOzHen9SSuAk">
