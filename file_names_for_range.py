def file_names_for_range(beg_yr, beg_mth, end_yr, end_mth):
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
        file_list += [month + str(beg_yr) + 'pub.dat' for month in included_months]
    else:
        first_year_months = months[months.index(beg_mth):]
        file_list += [month + str(beg_yr) + 'pub.dat' for month in first_year_months]

        for i in range(1,end_yr-beg_yr):
            current_yr = beg_yr + i
            file_list += [month + str(current_yr) + 'pub.dat' for month in months]

        end_year_months = months[:months.index(end_mth)+1]
        file_list += [month + str(end_yr) + 'pub.dat' for month in end_year_months]

    return file_list
