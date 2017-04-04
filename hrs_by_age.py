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
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import os

'''
------------------------------------------------------------------------
    Functions
------------------------------------------------------------------------
'''


def hrs_by_age(age_bins, beg_mmyy, end_mmyy, graph):
    '''
    --------------------------------------------------------------------
    Generates a vector of average hours of work by age for a given
    vector of age bins and a given time period (number of monthly CPS
    surveys)
    --------------------------------------------------------------------
    INPUTS:
    age_bins = ?
    beg_mmyy = ?
    end_mmyy = ?
    graph    = boolean, =True if save plot of hrs_age

    OTHER FUNCTIONS AND FILES CALLED BY THIS FUNCTION: None

    OBJECTS CREATED WITHIN FUNCTION:
    ? = ?

    FILES CREATED BY THIS FUNCTION: None

    RETURNS: hrs_age
    --------------------------------------------------------------------
    '''
    S = age_bins.shape[0]
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
