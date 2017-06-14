# Module to generate vector of hours worked by age from CPS data
This repository contains the work for creating a Python module that contains a function `hrs_by_age()` that takes as inputs a vector of age cutoffs, a "monYY" alphanumerical string beginning CPS survey month to use and a "monYY" alphanumerical string ending CPS survey month to use (such as "mar16"). This function returns a vector of average hours by age group that is the same size as the vector of age cutoffs.

The CPS data files are available on the NBER CPS data page at [http://nber.org/data/cps_basic.html](http://nber.org/data/cps_basic.html). The URL for each file and the format for a given month of the data file (compressed .zip) is `http://nber.org/cps-basic/monYYpub.zip`, where "mon" is the lower-case first three letters of a given month and "YY" are the last two digits of the four-digit year. For example, the data for the January 2017 survey compressed data file is [http://nber.org/cps-basic/jan17pub.zip](http://nber.org/cps-basic/jan17pub.zip).

When the compressed file is unzipped, the resulting data file has the form "monYYpub.dat". These .dat files are fixed with text files. The dictionary for the beginning column number of each variable for data from January 2015 on is available at [http://nber.org/data/progs/cps-basic/cpsbjan2015.dct](http://nber.org/data/progs/cps-basic/cpsbjan2015.dct). Value labels for some of the variables for data from January 2015 on are available at [http://nber.org/data/progs/cps-basic/cpsbjan2015.do](http://nber.org/data/progs/cps-basic/cpsbjan2015.do).

## Rules for calculating Total Usual Weekly Hours
The rules for the data that are used to calculate usual weekly hours are the following. The three key variables are:

* `PEHRUSL1`: "How many hours per week do you usually work at your main job?"
  * -4: hours vary
  * -1: n/a
  * 0-99: weekly hours
* `PEHRUSL2`: "How many hours per week do you usually work at your other job(s)?"
  * -4: hours vary
  * -1: n/a
  * 0-99: weekly hours
* `PEHRFTPT`: "Do you usually  work 35 hours or more per week?"
  * 1: Yes
  * 2: No
  * 3: Hours vary

Note that the CPS basic household survey data include a variable `PEHRUSLT` that is the sum of `PEHRUSL1` and `PEHRUSL2`. However, the variable `PEHRUSLT` excludes information when `PEHRFTPT=1` and either `PEHRUSL1` or `PEHRUSL2` equals -1 or -4. For this reason, we construct our own measure of usual weekly hours by age.

The following table describes our heuristic for computing total usual weekly hours `TotWklyHours`.

| `PEHRUSL1` | `PEHRUSL2` | `PEHRFTPT` | `TotWklyHours` |
|:----------:|:----------:|:----------:| --------------:|
|      -4    |      -4    |        1   | 35.0 |
|      -4    |      -4    |   2 or 3   | NaN |
|      -4    |      -1    |        1   | 35.0 |
|      -4    |      -1    |   2 or 3   | NaN |
|      -4    |    0-99    |        1   | max(`PEHRUSL2`, 35.0) |
|      -4    |    0-99    |   2 or 3   | `PEHRUSL2` |
|      -1    |      -4    |        1   | 35.0 |
|      -1    |      -4    |   2 or 3   | NaN |
|      -1    |      -1    |        1   | 35.0 |
|      -1    |      -1    |   2 or 3   | NaN |
|      -1    |    0-99    |        1   | max(`PEHRUSL2`, 35.0) |
|      -1    |    0-99    |   2 or 3   | `PEHRUSL2` |
|    0-99    |      -4    |        1   | max(`PEHRUSL1`, 35.0) |
|    0-99    |      -4    |   2 or 3   | `PEHRUSL1` |
|    0-99    |      -1    |        1   | max(`PEHRUSL1`, 35.0) |
|    0-99    |      -1    |   2 or 3   | `PEHRUSL1` |
|    0-99    |    0-99    |        1   | max(`PEHRUSL1` + `PEHRUSL2`, 35.0) |
|    0-99    |    0-99    |   2 or 3   | `PEHRUSL1` + `PEHRUSL2` |

## Inputs and Outputs of the module
Once the vector has been created, it will be pickled in a dictionary along with the parameters used to create the vector and saved in the `OUTPUT` folder.

As an alternative to manually downloading the data, the `web` variable can be set to true and the files will be fetched from the CPS website and stored temporarily while the function is running. The files will be deleted once the vector has been returned.

If the `graph` variable is set to true, a graph of the the average number of weekly hours by age will be created and saved to the `OUTPUTS/images` folder. The default plot that will be included is a html file produced by Bokeh. By altering `graph_type` to be equal to `plt`, a matplotlib plot will be generated instead.

Age bins can be set by passing a Numpy array into the function as the `age_bins` variable. The values in the array represent the lower bound of each bin.

The `l_tilde` variable acts as a normalizing parameter and can be sent to any number greater than 1 that the user would like to use as the model time endowment.
