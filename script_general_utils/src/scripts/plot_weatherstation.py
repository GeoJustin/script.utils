"""****************************************************************************
 Name:         plotWeatherStation
 Purpose:     
 
Created:         Oct 14, 2013
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
from datetime import datetime, date, timedelta # Plot Date & Time
from base64 import b64decode as readpassword               
import psycopg2 as DBase # PostgreSQL Connection

import paramiko # SSH Connection

import matplotlib.pyplot as draw # Plotting operations
import matplotlib.dates as mdates # Format Plot Date

import numpy # Plot Statistics

"""------------------------------------------------------------------------- """
""" Initialize variables and set switches open / closed"""

num_days = 30 # number of days to plot (current - n)

# Database Connection Parameters
host = r'thor.gi.alaska.edu'
base = r'spatial_database'
user = r'guest'
word = readpassword(r'Z3Vlc3Q=')

# Secure Shell Connection Parameters
ssh_ftp = r'ftp.gi.alaska.edu'
ssh_port = 22
ssh_user = r'jrich'
ssh_word = readpassword(r'SkxSaWNoMjAxMA==')

# Folder Paths: Local - local file folder and Server is the folder on the web server
local_folder = r'A:\Project_Database\Website\web_images\weatherstations' # Local Folder
server_folder = r'public_html/web_images/weatherstations'                # Server Folder

# Weather Stations to be plotted
weather_stations = ['ValdezCRREL', 'CordovaCRREL', 'ColumbiaCRREL']

# Process Switches True is open and False is closed
process = {'temperature': True, 
           'radiation': True,
           'relative_humidity': True}

# Set the current date and time for use throughout the script
current_date = date.today()

# Create database connection
connection  = DBase.connect(" host='%s' dbname='%s' user='%s' password='%s'" %(host, base, user, word))
cursor = connection.cursor() # Cursor object


"""------------------------------------------------------------------------- """


def get_plotdata (queryresults):
    """ Given queary results, create two arrays to serve as x and y datasets for 
    plotting. Generally this should consist of an x array of dates and a y 
    array of values. This callback returns a tuple containing both new arrays"""
    x_data = numpy.array([i[0] for i in queryresults if i[1] <> None])
    y_data = numpy.array([float(i[1]) for i in queryresults if i[1] <> None])
    return x_data, y_data


def get_statistics (array):
    """Given a one dimensional array of values, this call back returns 
    a dictionary statistics"""
    statistics = {}
    statistics ['mean'] = round (numpy.mean(array), 2)   # Find the mean value
    statistics ['max'] = round (numpy.max(array), 2)     # Find the maximum value
    statistics ['min'] = round (numpy.min(array), 2)     # Find the Minimum Value
    return statistics


def setup_plot (station, plottype):
    """Setup basic plot parameters that are the same in every plot. This 
    information (title, time generated... etc.) will be generated whether
    the data exists or not. In this way a record of data, or lack of data,
    is generated no matter what. This callback returns a reference to the 
    current figure"""
    figure = draw.figure(figsize=(8,4), dpi=300)
       
    # format the tick marks on the X-Axis and format them to display abbr. month
    axis = draw.gca() # Get Current Axis (GCA)
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))  
    axis.xaxis.set_major_locator(mdates.DayLocator())           # Major tick marks
    axis.xaxis.set_minor_locator(mdates.HourLocator())          # Minor tick marks
    
    draw.subplots_adjust(bottom = 0.2) # Adjust plot margins (make room for data values
    draw.xlim(current_date-timedelta(days=num_days), current_date) # Set x-axis range

    # Format and Label the Plot
    draw.rc("font", size=8) # Set default font size to 8px (rc = plot defaults)
    draw.suptitle('Weather Station %s: %s' %(station, plottype), fontsize=14)  # Title
    draw.xlabel('Date',fontsize=12)  # Y-Axis Label
    draw.ylabel('%s' %(plottype),fontsize=12) # X-Axis Label
        
    # Set local time the plot was last updated or created
    now = datetime.now().strftime("%B %d, %Y at %I:%M:%S %p")
    figure.text(0.5, 0.01, 'Plot Generated: %s' %(now), ha = 'center')
    
    return figure


def post_figure (figure):
    """ Create Secure Shell Connection to the web server and then ftp
    the figure to the correct folder"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Auto get host key
    ssh.connect(ssh_ftp, port=ssh_port, username=ssh_user, password=ssh_word) # Login
       
    ftp = ssh.open_sftp() # Create FTP connection to the server using SSH
    # Copy file from local workspace to server workspace
    ftp.put(r'%s/%s'%(local_folder, figure), r'%s/%s'%(server_folder, filename))
      
    ftp.close() # Close FTP Connection
    ssh.close() # Close SSH Connection
        
        
"""------------------------------------------------------------------------- """
        
        
if process['temperature'] == True:
    """If process temperature is set to open (true) a graph is generated depicting 
    the temperature at a given station along with it's back up temperature"""
    
    # For each station in weather station list
    for station in weather_stations:
        filename = 'weatherstation_%s_temperature.png' %(station)
        
        # SQL to query Weather Station Information
        cursor.execute("""SELECT date, air_temperature FROM weatherstation_data WHERE station_name = '%s' AND date > CURRENT_DATE - %s ORDER BY date ASC""" %(station, num_days))
        table_date, table_temp = get_plotdata (cursor.fetchall()) # Fetch the results and format to arrays
        
        # SQL to retrieve BACKUP Weather Station Information
        cursor.execute("""SELECT date, air_temperature FROM weatherstation_data WHERE station_name = '%s_BKP' AND date > CURRENT_DATE - %s ORDER BY date ASC""" %(station, num_days))
        BKP_table_date, BKP_table_temp = get_plotdata (cursor.fetchall()) # Fetch the results and format to arrays
        
        figure = setup_plot(station, 'Temperature')
    
        # Only plot data and statistics on the figure if there is data (size of 0 is empty)
        if table_date.size <> 0: 
            # Add text values to figure 
            stats = get_statistics (table_temp)
            figure.text(0.5, 0.07, 'Average Temp: %s    Minimum Temp: %s    Maximum Temp: %s' % (stats['mean'], stats['min'], stats['max']), ha = 'center')
            
            # Plot the data on the figure
            draw.plot (table_date, table_temp, color="red", label= 'Temperature') # Plot data
        
        # The the value array is empty print 'No Data' 
        else: figure.text(0.5, 0.07, 'Average Temp: No Data    Minimum Temp: No Data    Maximum Temp: No Data', ha = 'center')
        # No data points plotted to the figure in the else clause
          
        # Only plot BACKUP data and statistics on the figure if there is data (size of 0 is empty)
        if BKP_table_date.size <> 0: 
            # Add text values to figure 
            stats = get_statistics (table_temp)
            figure.text(0.5, 0.04, 'BACKUP: Average Temp: %s    Minimum Temp: %s    Maximum Temp: %s' % (stats['mean'], stats['min'], stats['max']), ha = 'center')
     
            # Plot the data on the figure
            draw.plot (BKP_table_date, BKP_table_temp, color="blue", label= 'Backup Temperature') # Plot data
        
        # The the value array is empty print 'No Data' 
        else: figure.text(0.5, 0.04, 'BACKUP: Average Temp: No Data    Minimum Temp: No Data    Maximum Temp: No Data', ha = 'center')
        # No data points plotted to the figure in the else clause
            
        # Add a legend to the plot
        if table_date.size <> 0 or BKP_table_date.size <> 0: 
            draw.legend(loc='upper left',prop={'size':8}, shadow=True)
        
        figure.savefig(r'%s\%s' %(local_folder, filename))  # Save the plot
        draw.close() # Release the drawing from memory
    
        post_figure (filename) # Post the figure to the web

        
        
if process['radiation'] == True:
    """If process radiation is set to open (true) a graph is generated depicting 
    the input solar radiation at a given station along with it's output solar radiation"""
    
    # For each station in weather station list
    for station in weather_stations:
        filename = 'weatherstation_%s_radiation.png' %(station)
        
        # SQL to query Weather Station Information      
        cursor.execute("""SELECT date, solar_radiation_in FROM weatherstation_data WHERE station_name = '%s' AND date > CURRENT_DATE - %s ORDER BY date ASC""" %(station, num_days))
        IN_table_date, IN_table_value = get_plotdata (cursor.fetchall()) # Fetch the results and format to arrays

        # SQL to retrieve BACKUP Weather Station Information  
        cursor.execute("""SELECT date, solar_radiation_out FROM weatherstation_data WHERE station_name = '%s' AND date > CURRENT_DATE - %s ORDER BY date ASC""" %(station, num_days))
        OUT_table_date, OUT_table_value = get_plotdata (cursor.fetchall()) # Fetch the results and format to arrays
           
        figure = setup_plot(station, 'Solar Radiation')
     
        # Only plot data and statistics on the figure if there is data (size of 0 is empty)
        if IN_table_date.size <> 0: 
            # Add text values to figure 
            stats = get_statistics (IN_table_value)
            figure.text(0.5, 0.07, 'IN: Average Radiation: %s    Minimum Radiation: %s    Maximum Radiation: %s' % (stats['mean'], stats['min'], stats['max']), ha = 'center')
             
            # Plot the data on the figure
            draw.plot (IN_table_date, IN_table_value, color="red", label= 'Radiation In') # Plot data
         
        # The the value array is empty print 'No Data' 
        else: figure.text(0.5, 0.07, 'IN: Average Radiation: No Data    Minimum Radiation: No Data    Maximum Radiation: No Data', ha = 'center')
        # No data points plotted to the figure in the else clause
           
        # Only plot BACKUP data and statistics on the figure if there is data (size of 0 is empty)
        if OUT_table_date.size <> 0: 
            # Add text values to figure 
            stats = get_statistics (OUT_table_value)
            figure.text(0.5, 0.04, 'OUT: Average Radiation: %s    Minimum Radiation: %s    Maximum Temp: %s' % (stats['mean'], stats['min'], stats['max']), ha = 'center')
      
            # Plot the data on the figure
            draw.plot (OUT_table_date, OUT_table_value, color="blue", label= 'Radiation Out') # Plot data
         
        # The the value array is empty print 'No Data' 
        else: figure.text(0.5, 0.04, 'OUT: Average Radiation: No Data    Minimum Radiation: No Data    Maximum Radiation: No Data', ha = 'center')
        # No data points plotted to the figure in the else clause
             
        # Add a legend to the plot
        if IN_table_date.size <> 0 or OUT_table_date.size <> 0: 
            draw.legend(loc='upper left',prop={'size':8}, shadow=True)
         
        figure.savefig(r'%s\%s' %(local_folder, filename))  # Save the plot
        draw.close() # Release the drawing from memory
     
        post_figure (filename) # Post the figure to the web



if process['relative_humidity'] == True:
    """If process umidity is set to open (true) a graph is generated depicting 
    the humidity at a given station"""
    
    # For each station in weather station list
    for station in weather_stations:
        filename = 'weatherstation_%s_humidity.png' %(station)
        
        # SQL to query Weather Station Information      
        cursor.execute("""SELECT date, relative_humidity FROM weatherstation_data WHERE station_name = '%s' AND date > CURRENT_DATE - %s ORDER BY date ASC""" %(station, num_days))
        table_date, IN_table_value = get_plotdata (cursor.fetchall()) # Fetch the results and format to arrays
           
        figure = setup_plot(station, 'Relative Humidity')
     
        # Only plot data and statistics on the figure if there is data (size of 0 is empty)
        if table_date.size <> 0: 
            # Add text values to figure 
            stats = get_statistics (IN_table_value)
            figure.text(0.5, 0.07, 'IN: Average Humidity: %s    Minimum Humidity: %s    Maximum Humidity: %s' % (stats['mean'], stats['min'], stats['max']), ha = 'center')
             
            # Plot the data on the figure
            draw.plot (table_date, IN_table_value, color="red", label= 'Humidity') # Plot data
         
        # The the value array is empty print 'No Data' 
        else: figure.text(0.5, 0.07, 'IN: Average Humidity: No Data    Minimum Humidity: No Data    Maximum Humidity: No Data', ha = 'center')
        # No data points plotted to the figure in the else clause
             
        # Add a legend to the plot
        if table_date.size <> 0:
            draw.legend(loc='upper left',prop={'size':8}, shadow=True)
         
        figure.savefig(r'%s\%s' %(local_folder, filename))  # Save the plot
        draw.close() # Release the drawing from memory
     
        post_figure (filename) # Post the figure to the web



connection.close() # Close Database Connection