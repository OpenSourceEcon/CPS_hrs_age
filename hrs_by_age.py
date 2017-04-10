'''
------------------------------------------------------------------------
This module generates a vector of average hours of work by age for a
given vector of age bins and a given time period (number of monthly CPS
surveys).

This Python module imports the following module(s):
    ?

This Python module defines the following function(s):
    ?
------------------------------------------------------------------------
'''
# Import packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import os

'''
------------------------------------------------------------------------
    Functions
------------------------------------------------------------------------
'''

filename = '/Users/rwe/Downloads/jan16pub.dat'
names = ('HWHHWGT', 'PRTAGE', 'PRTFAGE', 'PEHRUSL1', 'PEHRUSL2',
         'PEHRFTPT')
colspecs = ((46, 56), (121, 123), (123, 124), (217, 219),
            (219, 221), (221, 223))
df = pd.read_fwf(filename, colspecs=colspecs, header=None, names=names,
                 index_col=False)

# Drop all observations that:
#   1) have no hours in either response (PEHRUSL1=-1) and (PEHRUSL2=-1)
#   2) have [(PEHRUSL1=-1), (PEHRUSL2=-4), and (PEHRFTPT!=1)] or
#           [(PEHRUSL1=-4), (PEHRUSL2=-1), and (PEHRFTPT!=1)]
#   3) have age that is top-coded (PRTFAGE=1)
df = df[((df['PEHRUSL1'] >= 0) | (df['PEHRUSL2'] >= 0) |
        (df['PEHRFTPT'] == 1)) & (df['PRTFAGE'] == 0)]

# Create empty total weekly hours series that has the index from df
TotWklyHours = pd.Series(data=[np.nan], index=df.index)

# Assume that observations that report at least 35 hours of work in the
# typical week (PEHRFTPT=1) but report either n/a hours (-1) or varying
# hours (-4) have a supply of 35.0 hours per week
TotWklyHours[(df['PEHRUSL1'] < 0) & (df['PEHRUSL2'] < 0) &
             (df['PEHRFTPT'] == 1)] = 35.0

# Assume that observations that report at least 35 hours of work in the
# typical week (PEHRFTPT=1) but report only positive hours in job 1
# (PEHRUSL1>=0) and report n/a or varying hours in job 2 (PEHRUSL2<0)
# have a supply of the maximum of PEHRUSL1 and 35.0
TotWklyHours[(df['PEHRUSL1'] >= 0) & (df['PEHRUSL2'] < 0) &
             (df['PEHRFTPT'] == 1)] = np.maximum(35.0, df['PEHRUSL1'])

# Assume that observations that report at least 35 hours of work in the
# typical week (PEHRFTPT=1) but report n/a or varying hours in job 1
# (PEHRUSL1<0) and report only positive hours hours in job 2
# (PEHRUSL2>=0) have a supply of the maximum of PEHRUSL2 and 35.0
TotWklyHours[(df['PEHRUSL1'] < 0) & (df['PEHRUSL2'] >= 0) &
             (df['PEHRFTPT'] == 1)] = np.maximum(35.0, df['PEHRUSL2'])

# Observations that report only positive hours in job 1 (PEHRUSL1>=0)
# and report n/a or varying hours in job 2 (PEHRUSL2<0) and do not
# report at least 35 hours of work in the typical week (PEHRFTPT!=1)
# have hours given by PEHRUSL1
TotWklyHours[(df['PEHRUSL1'] >= 0) & (df['PEHRUSL2'] < 0) &
             (df['PEHRFTPT'] != 1)] = df['PEHRUSL1']

# Observations that report n/a or varying hours in job 1 (PEHRUSL1<0)
# and report only positive hours in job 2 (PEHRUSL2>=0) and do not
# report at least 35 hours of work in the typical week (PEHRFTPT!=1)
# have hours given by PEHRUSL2
TotWklyHours[(df['PEHRUSL1'] < 0) & (df['PEHRUSL2'] >= 0) &
             (df['PEHRFTPT'] != 1)] = df['PEHRUSL2']

# Observations that report positive hours in job 1 (PEHRUSL1>=0) and
# positive hours in job 2 (PEHRUSL2>=0) and report at least 35 hours of
# work in the typical week (PEHRFTPT=1) have hours given by the maximum
# of PEHRUSL1+PEHRUSL2 and 35.0
TotWklyHours[(df['PEHRUSL1'] >= 0) & (df['PEHRUSL2'] >= 0) &
             (df['PEHRFTPT'] == 1)] = np.maximum(35.0, df['PEHRUSL1'] +
                                                 df['PEHRUSL2'])

# Observations that report positive hours in job 1 (PEHRUSL1>=0) and
# positive hours in job 2 (PEHRUSL2>=0) and do not report at least 35
# hours of work in the typical week (PEHRFTPT!=1) have hours given by
# PEHRUSL1+PEHRUSL2
TotWklyHours[(df['PEHRUSL1'] >= 0) & (df['PEHRUSL2'] >= 0) &
             (df['PEHRFTPT'] != 1)] = df['PEHRUSL1'] + df['PEHRUSL2']

# Add TotWklyHours to DataFrame
df['TotWklyHours'] = TotWklyHours

df_hrs_age = df.groupby('PRTAGE').apply(lambda x:
                                        np.average(x.TotWklyHours,
                                                   weights=x.HWHHWGT))

# Create directory if images directory does not already exist
cur_path = os.path.split(os.path.abspath(__file__))[0]
output_fldr = 'images'
output_dir = os.path.join(cur_path, output_fldr)
if not os.access(output_dir, os.F_OK):
    os.makedirs(output_dir)

# Plot steady-state consumption and savings distributions
min_age = df_hrs_age.index.min()
max_age = df_hrs_age.index.max()
age_pers = np.arange(min_age, max_age + 1)
# age_pers = np.arange(1, S + 1)
fig, ax = plt.subplots()
plt.plot(age_pers, df_hrs_age, label='Average hours by age')
# for the minor ticks, use no labels; default NullFormatter
minorLocator = MultipleLocator(1)
ax.xaxis.set_minor_locator(minorLocator)
plt.grid(b=True, which='major', color='0.65', linestyle='-')
plt.title('Average hours by age $s$', fontsize=20)
plt.xlabel(r'Age $s$')
plt.ylabel(r'Average hours')
plt.xlim((min_age - 1, max_age + 1))
# plt.ylim((-1.0, 1.15 * (b_ss.max())))
plt.legend(loc='upper right')
output_path = os.path.join(output_dir, 'hrs_by_age')
plt.savefig(output_path)
# plt.show()
plt.close()



def hrs_by_age(age_bins, l_tilde, beg_mmyy, end_mmyy, web=True,
               directory=None, graph=False):
    '''
    --------------------------------------------------------------------
    Generates a vector of average hours of work by age for a given
    vector of age bins and a given time period (number of monthly CPS
    surveys)
    --------------------------------------------------------------------
    INPUTS:
    age_bins = (S,) vector, beginning cutoff ages for each age bin
    l_tilde  = scalar > 1, model time endowment for each life period
    beg_mmyy = length 4 string, numeric two-digit month and numeric
               last-two-digits of four-digit year for beginning month-
               year of data period
    end_mmyy = length 4 string, numeric two-digit month and numeric
               last-two-digits of four-digit year for ending month-year
               of data period
    web      = boolean, =True if get data from NBER data website
    dir      = string, directory of local folder where data reside
    graph    = boolean, =True if save plot of hrs_age

    OTHER FUNCTIONS AND FILES CALLED BY THIS FUNCTION: None

    OBJECTS CREATED WITHIN FUNCTION:
    ? = ?

    FILES CREATED BY THIS FUNCTION: None

    RETURNS: hrs_age
    --------------------------------------------------------------------
    '''
    if web:
        # Throw and error if the machine is not connected to the
        # internet
        if not_connected:
            err_msg = ('ERROR: No local directory was specified as the ' +
                   'source for the data.')
        raise RuntimeError(err_msg)
    elif not web and directory==None:
        err_msg = ('hrs_by_age() ERROR: No local directory was ' +
                   'specified as the source for the data.')
        raise RuntimeError(err_msg)
    elif not web and directory!=None:
        # Check to make sure the necessary files are present in the
        # local directory. If not, throw error. If so, go on with
        # analysis

    S = age_bins.shape[0]
    beg_yr = int(beg_mmyy[-2:])
    beg_mth = beg_mmyy[:-2]
    end_yr = int(end_mmyy[-2:])
    end_mth = end_mmyy[:-2]
    file_list = ['mar16pub.dat']
    for name in file_list:
        filename = os.path.join(directory, name)

    hrs_age = age_bins

    if graph:
        '''
        ----------------------------------------------------------------
        cur_path    = string, path name of current directory
        output_fldr = string, folder in current path to save files
        output_dir  = string, total path of images folder
        output_path = string, path of file name of figure to be saved
        age_pers    = (S,) vector, ages from 1 to S
        ----------------------------------------------------------------
        '''
        # Create directory if images directory does not already exist
        cur_path = os.path.split(os.path.abspath(__file__))[0]
        output_fldr = 'images'
        output_dir = os.path.join(cur_path, output_fldr)
        if not os.access(output_dir, os.F_OK):
            os.makedirs(output_dir)

        # Plot steady-state consumption and savings distributions
        age_pers = np.arange(1, S + 1)
        fig, ax = plt.subplots()
        plt.plot(age_pers, hrs_age, label='Average hours by age')
        # for the minor ticks, use no labels; default NullFormatter
        minorLocator = MultipleLocator(1)
        ax.xaxis.set_minor_locator(minorLocator)
        plt.grid(b=True, which='major', color='0.65', linestyle='-')
        plt.title('Average hours by age $s$', fontsize=20)
        plt.xlabel(r'Age $s$')
        plt.ylabel(r'Average hours')
        plt.xlim((0, S + 1))
        # plt.ylim((-1.0, 1.15 * (b_ss.max())))
        plt.legend(loc='upper right')
        output_path = os.path.join(output_dir, 'hrs_by_age')
        plt.savefig(output_path)
        # plt.show()
        plt.close()

    return hrs_age
