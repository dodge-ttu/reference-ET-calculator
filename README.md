# Reference ET (ETo) Calculation via FAO-56 and Python

<img src="https://drive.google.com/uc?id=1TLUYQ7uSpISZI2V3CVF15XrhhiJPENj1">

### Will Dodge Spring 2018 ###

---

### Overview

Evapotranspiration (ET) is a term used in agriculture to describe total evaporation from soil and plant surfaces over time. This value is estimated from four basic climate parameters: solar radiation, air temp, wind speed, and relative humidity. Understanding how much water is leaving an agricultural system on a daily basis is fundamental to efficient crop management. The development of a reasonable ET model began more than a century ago and continues today. The Food and Agriculture Organization of the United Nations has developed a method for calculating evapotranspiration (ET) as well as the more useful reference evapotranspiration (ETo). The official name of the ETo model supported by the united nations is <a href="http://www.fao.org/docrep/X0490E/X0490E00.htmFAO-56">FAO-56</a>.

In February of 2010 the researchers at the University of Florida Institute of Food and Agricultural Sciences published a 
<a href="https://drive.google.com/file/d/1EVjUARYY0g5o0ioVy70yANynh8DAQ4ir/view?usp=sharing">beautiful paper</a> detailing a step by step method for calculating ETo based on the FAO-56 model. The crux of the model is the requirement for clean climate data for the four key parameters. Weather data is widely available but not always complete or in units appropriate for FAO-56. Python is a powerful programming language with superior data wrangling capacity. Here we leverage the power of Python to clean and organize daily climate data, calculate ETo, and build widgets suitable for use in a <a href="jupyter.org">Jupyter Notebook</a>.

---

### Observation data required

The required parameters for calculating ET<sub>o</sub> are solar radiation, wind speed, air temperature, and relative humididity. The specifics of these observations is well documented in the publication this model is based upon. In the event that one is missing data or entire parameters the official documentation at the <a href="http://www.fao.org/docrep/X0490E/x0490e00.htm#Contents">FAO website</a> sould be consulted to determine the approach to calculating ETO without said missing variable. In this guide a link is provided so that users can read a test csv from URL meaning tha one does not need a weather data set of their own to work through this tutorial.

#### The chart below describes the weather data required

<img src="https://drive.google.com/uc?id=1scDh_GzljhJ6AyVDlQz-k_ZadNvyW6Sc">

### Import required libraries

```
from datetime import datetime
from matplotlib import pyplot as plt
import pandas as pd
import math
import numpy as np
from scipy import stats
from IPython.display import Markdown, display
import numpy.polynomial.polynomial as poly
import ipywidgets as widgets
from IPython.display import display, HTML
import qgrid
````
### Read weather data into Pandas data frame

In this script the raw <code>.csv</code> data is coming from a google drive shareable link. This is <b>great</b> because the notebook itself can be distributed without needing to also distrubute a slew of assocaited file data. The other thing is that <b>users who execute this code will not have to adjust the filepath given</b> to the <code>pd.read_csv()</code> command.

```
DF = pd.read_csv("https://drive.google.com/uc?id=1K7vnCpK8tElmE-VfyMiN4pQSQEAkOrTE")
```

---

### The test data needs to be cleaned

In the test data set included in this tutorial has some issues. Most large weather data sets will have some sort of cleaning that needs to be done. This may be interpoloating missing values, changing time resolution, or removing known bad values like -9999. In the case of this test data we have several issues. There are missing values, the time is missing a colon to separate the minutes from the seconds, the time step is 15 minutes and we need daily time series data, the units are not correct, and there are known bad values. 

#### Let's begin by fixing the time

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

#### Python only understands 00-23 hour days

Python only reads datetime with hours <code>00:00 - 23:59 (HH:MM - HH:MM)</code>, for example <code>23:15</code> is fine for 23rd hour and 15th minute. Our data contains <code>24:00</code> which will not work so <b>one option</b> is to change <code>24:00</code> to <code>23:39</code>. This is appropriate in this case becuse we are scailing the data up with regard to the time step as well as beacuse our date begins at zero and ends at the 23rd hour. Now the datetime parser will be able to covert our dates, which are strings, into a propper datetime series. If we wanted, we could change the time to <code>23:59:59 (HH:MM:SS)</code> so that we would only be altering the series by a single second. That is not necessary here because we are scaling to a daily time step.

```
def change_24(time_with_colon):
    """ Change the 24:00 times in data to 23:59.
    
    :param time_with_colon: a pandas series of strings representing HH:MM containing 24:00 values
    """
    
    TimeNo24 = []
    for i in DF[time_with_colon]:
        if i == "24:00":
            i = "23:59"
        else:
            i = i
    TimeNo24.append(i)
    
    return TimeNo24
    
# Run function and remove 24:00
    
DF["TimeNo24"] = change_24(DF["TimeWColon"]
```

#### Concantonate date and time strings for parsing

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

### 









         



         
         
         
             











         
   
