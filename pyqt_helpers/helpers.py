import numpy as np
import pandas as pd

###################################### HELPER FUNCTIONS ######################################

def find_grid_dims(num_elements, num_cols):
    """Method to determine the number of rows we need in a grid given the number of elements and the number of columns

    Args:
        num_elements (int): How many elements we want to split
        num_cols (int): How many columns across which we want to split them

    Returns:
        num_rows (int): Number of rows needed in the grid
        
        **num_cols**: *int*  Number of columns needed in the grid
    """    

    num_rows = num_elements / num_cols
    # If the last number of the fraction is a 5, add 0.1. This is necessary because Python defaults to 
    # "bankers rounding" (rounds 2.5 down to 2, for example) so would otherwise give us too few rows
    if str(num_rows).split('.')[-1] == '5':
        num_rows += 0.1
    num_rows = round(num_rows)

    return num_rows, num_cols

def epoch_to_pacific_time(time, y_data=None):
    """Method to convert from epoch (UTC, number of seconds since Jan 1, 1970) to a datetime format
    in the Pacific timezone. Can also take in an accompanying array of y_data to ensure any changes in shape
    that happen to the time (like removing np.nan values) also happens to the y_data.

    Args:
        time (array_like): Anything that can be converted into a np array and sliced, e.g a list of epoch times
        y_data (array_like): Can be an array of values or an array of arrays, either works

    Returns:
        t_pacific (DateTimeIndex): Datetime object in pacific time
    """
    # Convert to numpy array
    time = np.array(time)
    # Get rid of any np.nan present in t, it messes with the conversion
    nan_mask = np.invert(np.isnan(time))
    time = time[nan_mask]
    # If we've passed in y_data, apply the same mask to keep the arrays matching
    if y_data is not None:        
        # See if the first value of y_data has a length. If it does (no error), y_data is a list of lists.
        # If it throws a TypeError, it's a list of values
        try:
            len(y_data[0])
        # If y_data is an array of values, apply the mask directly
        except TypeError:
            y_data = np.array(y_data)[nan_mask]
        # If y_data is an array of arrays, apply the mask to each sub-array
        else:
            y_data = [np.array(y)[nan_mask] for y in y_data]
    # Convert t to datetime, specifying that it's in seconds
    t_datetime = pd.to_datetime(time, unit='s')
    # Current timezone is UTC
    t_utc = t_datetime.tz_localize('utc')
    # New timezone is pacific
    t_pacific = t_utc.tz_convert('America/Los_Angeles')

    return t_pacific, y_data