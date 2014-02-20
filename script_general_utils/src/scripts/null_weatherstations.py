"""****************************************************************************
 Name:         operations.null_weatherstations
 Purpose:     remove null data from table columns before plotting. This script
             is only needed to correct -9999 values added during data import.
 
Created:         Feb 20, 2014
Author:          Justin Rich (justin.rich@gi.alaska.edu)
Location: Geophysical Institute | University of Alaska, Fairbanks
Contributors:

Copyright:   (c) Justin L. Rich 2014
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
import psycopg2 as DBase # PostgreSQL Connection
from base64 import b64decode as readpassword   

# Database Connection Parameters
host = r'thor.gi.alaska.edu'
base = r'spatial_database'
user = r'script'
word = readpassword(r'c2NyaXB0')

connection  = DBase.connect(" host='%s' dbname='%s' user='%s' password='%s'" %(host, base, user, word))
cursor = connection.cursor() # Cursor object

#Remove negative -9999 from columns and replace it with null 
cursor.execute("""UPDATE weatherstation_data SET solar_radiation_in = NULL WHERE solar_radiation_in = -9999; """)
cursor.execute("""UPDATE weatherstation_data SET solar_radiation_out = NULL WHERE solar_radiation_out = -9999;""")
cursor.execute("""UPDATE weatherstation_data SET wind_speed = NULL WHERE wind_speed = -9999;""")
cursor.execute("""UPDATE weatherstation_data SET wind_direction = NULL WHERE wind_direction = -9999;""")

connection.close() # Close Database Connection