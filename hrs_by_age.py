'''
------------------------------------------------------------------------
This module generates a vector of average hours of work by age for a
given vector of age bins and a given time period (number of monthly CPS
surveys).
------------------------------------------------------------------------
'''
# Import packages
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
# from matplotlib.ticker import MultipleLocator
import os
import requests
from io import BytesIO
from zipfile import ZipFile
import urllib.request
from tempfile import NamedTemporaryFile
import pickle
from bokeh.plotting import figure, output_file, show

'''
------------------------------------------------------------------------
    Functions
------------------------------------------------------------------------
'''
def hrs_by_age(beg_mmyy, end_mmyy, web=True, directory=None, graph=False,
                age_bins = None, l_tilde = 1):
    '''
    --------------------------------------------------------------------
    Generates a vector of average hours of work by age for a given
    vector of age bins and a given time period (number of monthly CPS
    surveys)
    --------------------------------------------------------------------
    INPUTS:
    age_bins = (S,) vector, beginning cutoff ages for each age bin
    l_tilde  = scalar > 1, model time endowment for each life period
    beg_mmyy = length 5 string, alpha three-character month and numeric
               last-two-digits of four-digit year for beginning month-
               year of data period (i.e. 'jan16')
    end_mmyy = length 4 string, numeric two-digit month and numeric
               last-two-digits of four-digit year for ending month-year
               of data period
    web      = boolean, =True if get data from NBER data website
    dir      = string, directory of local folder where data reside
    graph    = boolean, =True if save plot of hrs_age

    OTHER FUNCTIONS AND FILES CALLED BY THIS FUNCTION: file_names_for_range

    FILES CREATED BY THIS FUNCTION: None

    RETURNS: hrs_age
    --------------------------------------------------------------------
    '''
    # S = age_bins.shape[0]
    beg_yr = int(beg_mmyy[-2:])
    beg_mth = beg_mmyy[:-2]
    end_yr = int(end_mmyy[-2:])
    end_mth = end_mmyy[:-2]
    file_paths = []

    if web:
        # Throw an error if the machine is not connected to the internet
        if not_connected():
            err_msg = ('hrs_by_age() ERROR: The local machine is not ' +
                       'connected to the internet and web=True was ' +
                       'selected.')
            raise RuntimeError(err_msg)

        file_urls = file_names_for_range(beg_yr, beg_mth, end_yr, end_mth, web)

        file_paths = fetch_files_from_web(file_urls)

    elif not web and directory==None:
        # Thow an error if no source of files is given
        err_msg = ('hrs_by_age() ERROR: No local directory was ' +
                   'specified as the source for the data.')
        raise RuntimeError(err_msg)

    elif not web and directory!=None:
        full_directory = os.path.expanduser(directory)
        file_list = file_names_for_range(beg_yr, beg_mth, end_yr, end_mth, web)

        for name in file_list:
            file_paths.append(os.path.join(full_directory, name))
        # Check to make sure the necessary files are present in the
        # local directory
        err_msg = ('hrs_by_age() ERROR: The file %s was not found in the directory %s')
        for path in file_paths:
            if not os.path.isfile(path):
                raise RuntimeError(err_msg % (path, full_directory))

    df_hrs_age = recalculate_avg_hours(file_paths, age_bins)

    df_hrs_age = df_hrs_age/l_tilde

    if graph:
        create_graph(df_hrs_age, age_bins)

    # Create OUTPUT/folder directory if does not already exist
    cur_path = os.path.split(os.path.abspath(__file__))[0]
    output_fldr = 'OUTPUT/'
    output_dir = os.path.join(cur_path, output_fldr)
    if not os.access(output_dir, os.F_OK):
        os.makedirs(output_dir)
    outputfile = os.path.join(output_dir, 'hrs_by_age.pkl')
    # Create output object as vector and parameters used to create it
    output_object = {'vector':df_hrs_age, 'beginning_month':beg_mmyy, 'ending_month':\
    end_mmyy, 'web':web, 'directory':directory, 'graph':graph, 'age_bins':age_bins, \
    'l_tilde':l_tilde}
    # Save output as pickle
    pickle.dump(output_object, open(outputfile, 'wb'))

    # remove temporary files
    if web:
        for path in file_paths:
            os.unlink(path)
            assert not os.path.exists(path)

    return None

def recalculate_avg_hours(file_paths, age_bins):
    names = ('HWHHWGT', 'PRTAGE', 'PRTFAGE', 'PEHRUSL1', 'PEHRUSL2',
             'PEHRFTPT')
    colspecs = ((46, 56), (121, 123), (123, 124), (217, 219),
                (219, 221), (221, 223))

    list_months_df = []
    for filename in file_paths:
        month_df = pd.read_fwf(filename, colspecs=colspecs, header=None, names=names,
                         index_col=False)
        list_months_df.append(month_df)

    # concatenate all dataframes
    df = pd.concat(list_months_df)

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

    if age_bins is not None:
        age_bins = np.append(age_bins, 80)
        age_bins = list(age_bins)
        df['age_bins'] = pd.cut(df['PRTAGE'], age_bins)
        df_hrs_age = df.groupby('age_bins').apply(lambda x:
                                            np.average(x.TotWklyHours,
                                                       weights=x.HWHHWGT))

    else:
        df_hrs_age = df.groupby('PRTAGE').apply(lambda x:
                                            np.average(x.TotWklyHours,
                                                       weights=x.HWHHWGT))

    return df_hrs_age

def not_connected(url='http://www.google.com/', timeout=5):
    '''
    --------------------------------------------------------------------
    Checks for internet connection of machine.
    --------------------------------------------------------------------
    INPUTS:
    url     = static, 'http://www.google.com/'
    timeout = static, 5 seconds

    RETURNS: bool
    --------------------------------------------------------------------
    '''
    try:
        _ = requests.get(url, timeout=timeout)
        return False
    except requests.ConnectionError:
        return True

def file_names_for_range(beg_yr, beg_mth, end_yr, end_mth, web):
    '''
    --------------------------------------------------------------------
    Creates list of desired filenames.
    --------------------------------------------------------------------
    INPUTS:
    beg_yr  = int, beginning year of desired files
    beg_mth = string, 3 character beginning month of desired files
    end_yr  = int, end year of desired files
    end_mth = string, 3 character beginning month of desired files
    web     = bool, whether or not files are being downloaded from the web

    RETURNS: file_list
    --------------------------------------------------------------------
    '''
    file_list = []

    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    if beg_yr < 15 or end_yr > 17:
        err_msg = ('hrs_by_age() ERROR: Dates out of range.')
        raise RuntimeError(err_msg)
    elif end_yr == 17 and months.index(end_mth) > 2:
        err_msg = ('hrs_by_age() ERROR: Dates out of range.')
        raise RuntimeError(err_msg)

    if beg_yr == end_yr:
        included_months = months[months.index(beg_mth):months.index(end_mth)+1]
        file_list += [month + str(beg_yr) + 'pub' for month in included_months]
    else:
        first_year_months = months[months.index(beg_mth):]
        file_list += [month + str(beg_yr) + 'pub' for month in first_year_months]

        for i in range(1,end_yr-beg_yr):
            current_yr = beg_yr + i
            file_list += [month + str(current_yr) + 'pub' for month in months]

        end_year_months = months[:months.index(end_mth)+1]
        file_list += [month + str(end_yr) + 'pub' for month in end_year_months]

    if web:
        file_list = ['http://nber.org/cps-basic/' + file_name + '.zip' for file_name in file_list]
    else:
        file_list = [file_name + '.dat' for file_name in file_list]

    return file_list

def fetch_files_from_web(file_paths):
    '''
    --------------------------------------------------------------------
    Fetches files from NBER website and saves them as temporary files.
    --------------------------------------------------------------------
    INPUTS:
    file_paths = list, paths of desired zip files

    FILES CREATED BY THIS FUNCTION: .pub file for each month of data

    RETURNS: local_paths = list, paths of temporary files
    --------------------------------------------------------------------
    '''
    local_paths = []

    for file_path in file_paths:
        # url = requests.get(file_path) (if using reuests package)
        url = urllib.request.urlopen(file_path)

        f = NamedTemporaryFile(delete=False)
        path = f.name

        # url.content (if using requests package)
        with ZipFile(BytesIO(url.read())) as zipped_file:
            for contained_file in zipped_file.namelist():
                for line in zipped_file.open(contained_file).readlines():
                    f.write(line)

        local_paths.append(path)

        f.close()

    return local_paths

def create_graph(df_hrs_age, age_bins):
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
    output_fldr = 'OUTPUT/images'
    output_dir = os.path.join(cur_path, output_fldr)
    if not os.access(output_dir, os.F_OK):
        os.makedirs(output_dir)

    # Plot steady-state consumption and savings distributions
    # min_age = df_hrs_age.index.min()
    # max_age = df_hrs_age.index.max()
    # age_pers = np.arange(min_age, max_age + 1)
    # # age_pers = np.arange(1, S + 1)
    # fig, ax = plt.subplots()
    # plt.plot(age_pers, df_hrs_age, label='Average hours by age')
    # # for the minor ticks, use no labels; default NullFormatter
    # minorLocator = MultipleLocator(1)
    # ax.xaxis.set_minor_locator(minorLocator)
    # plt.grid(b=True, which='major', color='0.65', linestyle='-')
    # plt.title('Average hours by age $s$', fontsize=20)
    # plt.xlabel(r'Age $s$')
    # plt.ylabel(r'Average hours')
    # # plt.xlim((0, S + 1))
    # plt.xlim((min_age - 1, max_age + 1))
    # # plt.ylim((-1.0, 1.15 * (b_ss.max())))
    # plt.legend(loc='upper right')
    # output_path = os.path.join(output_dir, 'hrs_by_age')
    # plt.savefig(output_path)
    # plt.close()


    output_path = os.path.join(output_dir, 'hrs_by_age.html')
    output_file(output_path)

    if age_bins is None:
        min_age = df_hrs_age.index.min()
        max_age = df_hrs_age.index.max()
        age_pers = np.arange(min_age, max_age + 1)
        p = figure(plot_width=400, plot_height=400, title='Average hours by age')
    else:
        age_bins = np.append(age_bins, 80)
        age_pers = []
        for i in range(len(age_bins)-1):
            age_range = '%d - %d' % (age_bins[i], age_bins[i+1]-1)
            age_pers.append(age_range)

        p = figure(plot_width=400, plot_height=400, x_range=age_pers, title='Average hours by age')

    p.xaxis.axis_label = 'Age'
    p.yaxis.axis_label = 'Average hours'
    p.line(age_pers, df_hrs_age, line_width=2)
    show(p)
