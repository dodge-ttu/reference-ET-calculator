# Reference ET (ETo) Calculation via FAO-56 and Python

<img src="https://drive.google.com/uc?id=1TLUYQ7uSpISZI2V3CVF15XrhhiJPENj1">

### Will Dodge Spring 2018 ###

---

### Overview

Evapotranspiration (ET) is a term used in agriculture to describe total evaporation from soil and plant surfaces over time. This value is estimated from four basic climate parameters: solar radiation, air temp, wind speed, and relative humidity. Understanding how much water is leaving an agricultural system on a daily basis is fundamental to efficient crop management. The development of a reasonable ET model began more than a century ago and continues today. The Food and Agriculture Organization of the United Nations has developed a method for calculating evapotranspiration (ET) as well as the more useful reference evapotranspiration (ETo). The official name of the ETo model supported by the united nations is <a href="http://www.fao.org/docrep/X0490E/X0490E00.htmFAO-56">FAO-56</a>.

In February of 2010 the researchers at the University of Florida Institute of Food and Agricultural Sciences published a 
<a href="https://drive.google.com/file/d/1EVjUARYY0g5o0ioVy70yANynh8DAQ4ir/view?usp=sharing">beautiful paper</a> detailing a step by step method for calculating ETo based on the FAO-56 model. The crux of the model is the requirement for clean climate data for the four key parameters. Weather data is widely available but not always complete or in units appropriate for FAO-56. Python is a powerful programming language with superior data wrangling capacity. Here we leverage the power of Python to clean and organize daily climate data, calculate ETo, and build widgets suitable for use in a <a href="jupyter.org">Jupyter Notebook</a>.

---

### Observation data required:

The required parameters for calculating ET<sub>o</sub> are solar radiation, wind speed, air temperature, and relative humididity. The specifics of these observations is well documented in the publication this model is based upon. In the event that one is missing data or entire parameters the official documentation at the <a href="http://www.fao.org/docrep/X0490E/x0490e00.htm#Contents">FAO website</a> sould be consulted to determine the approach to calculating ETO without said missing variable. In this guide a link is provided so that users can read a test csv from URL meaning tha one does not need a weather data set of their own to work through this tutorial.

#### The chart below describes the weather data required:

<img src="https://drive.google.com/uc?id=1scDh_GzljhJ6AyVDlQz-k_ZadNvyW6Sc">

### Import required libraries:

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
### Observation data required:

The required parameters for calculating ET<sub>o</sub> are solar radiation, wind speed, air temperature, and relative humididity. The specifics of these observations is well documented in the publication this model is based upon. In the event that one is missing data or entire parameters the official documentation at the <a href="http://www.fao.org/docrep/X0490E/x0490e00.htm#Contents">FAO website</a> sould be consulted to determine the approach to calculating ETO without said missing variable.

         
         
         
             











         
   
