"""****************************************************************************
 Name:         plot_mascons
 Purpose:     
 
Created:         Nov 1, 2013
Author:          Justin Rich (justin.rich@gi.alaska.edu)
Location: Geophysical Institute | University of Alaska, Fairbanks
Contributors:

Copyright:   (c) Justin L. Rich 2013
License:     Although this application has been produced and tested
 successfully, no warranty expressed or implied is made regarding the
 reliability and accuracy of the utility, or the data produced by it, on any
 other system or for general or scientific purposes, nor shall the act of
 distribution constitute any such warranty. It is also strongly recommended
 that careful attention be paid to the contents of the metadata / help file
 associated with these data to evaluate application limitations, restrictions
 or intended use. The creators and distributors of the application shall not
 be held liable for improper or incorrect use of the utility described and/
 or contained herein.
****************************************************************************"""
from base64 import b64decode as readpassword
import psycopg2 as DBase # PostgreSQL Connection

import matplotlib.pyplot as draw # Plotting operations
import matplotlib.dates as mdates # Format Plot Date

import numpy # Plot Statistics


"""GLOBAL-VARiABLES--------------------------------------------------------- """


# Database Connection Parameters
host = r'thor.gi.alaska.edu'
base = r'spatial_database'
user = r'guest'
word = readpassword(r'Z3Vlc3Q=')

# Folder Paths: Local - local file folder
local_folder = r'A:\Desktop\Test' # Local Folder

# Plot Labels and Titles
label = {'ylabel': 'cm w.e. (SUM)',
         'xlabel': 'Date (Year)'}

# Region Lookup
regions = {'region1': (1442,1443,1446,1447,1452,1453,1462,1463,1471,1472),
           'region2': (1479,1480,1481,1473), 
           'region3': (1482,1483,1484,1485), 
           'region4': (1454,1455,1464,1465,1466,1474,1475),                      # CHUGACH
           'region5': (1476,1477), 
           'region6': (1456,1457,1458,1459,1448,1449,1467,1468,1469,1470,1478),  # WRST
           'region7': (1460,1461,1450,1451), 
           'region8': (1444,1445,1439,1440,1441,1437,1438,1434,1435)}

# Create database connection
connection  = DBase.connect(" host='%s' dbname='%s' user='%s' password='%s'" %(host, base, user, word))
cursor = connection.cursor() # Cursor object


"""FUNCTIONS---------------------------------------------------------------- """


def get_plotdata (queryresults):
    """ Given queary results, create two arrays to serve as x and y datasets for 
    plotting. Generally this should consist of an x array of dates and a y 
    array of values. This callback returns a tuple containing both new arrays"""
    x_data = numpy.array([i[0] for i in queryresults if i[1] <> None])
    y_data = numpy.array([float(i[1]) for i in queryresults if i[1] <> None])
    return x_data, y_data


def setup_plot (region, title = ''):
    """Setup basic plot parameters that are the same in every plot. This 
    information (title, time generated... etc.) will be generated whether
    the data exists or not. In this way a record of data, or lack of data,
    is generated no matter what. This callback returns a reference to the 
    current figure"""
    figure = draw.figure(figsize=(8,4), dpi=300)
       
    # format the tick marks on the X-Axis and format them to display abbr. month
    axis = draw.gca() # Get Current Axis (GCA)
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  
    axis.xaxis.set_major_locator(mdates.YearLocator())           # Major tick marks
    axis.xaxis.set_minor_locator(mdates.MonthLocator())          # Minor tick marks
    
    # Format and Label the Plot
    draw.rc("font", size=8) # Set default font size to 8px (rc = plot defaults)
    draw.suptitle(title, fontsize=14)  # Title
    draw.xlabel(label['xlabel'],fontsize=12)  # Y-Axis Label
    draw.ylabel(label['ylabel'],fontsize=12) # X-Axis Label
    
    return figure


"""MAIN--------------------------------------------------------------------- """


for region, mascons in regions.iteritems():
    filename = 'Mascon_%s.png' %(region) # Assemble file name for saving
    
    where = ''# SQL where statement builder
    for mascon in mascons: # For each mascon in mascons listJ
        where += ' mascon = %s OR' %(mascon)
    where = where[0:-3] # Remove last or from the where statement

    # Get data from database
    cursor.execute("""SELECT date, SUM(values_filter1d) FROM mascon_solution WHERE %s GROUP BY date ORDER BY date;""" %(where))
    table_date, table_value = get_plotdata (cursor.fetchall()) # Fetch the results and format to arrays
            
    # Setup basic figure parameters
    figure = setup_plot(region, 'Mascon Region %s: cm w.e. vs date' %(region))
    
    # The the value array is empty print 'No Data' 
    draw.subplots_adjust(bottom = 0.2) # Adjust plot margins (make room for data values
    figure.text(0.5, 0.04, 'Mascons: %s'%(' , '.join(str(m) for m in mascons)), ha = 'center')
        
    # Plot the data on the figure
    draw.plot (table_date, table_value, color="red", label= 'cm w.e.') # Plot data

    figure.savefig(r'%s\%s' %(local_folder, filename))  # Save the plot
    draw.close() # Release the drawing from memory
     
connection.close() # Close Database Connection