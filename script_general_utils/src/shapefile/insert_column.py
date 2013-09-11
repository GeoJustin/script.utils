"""****************************************************************************
 Name: library.shp_insert_column
 Purpose: Insert a column into a shapefile. Position must be within the table.
    positions falling outside the length of the table will not be added.
 
Created: Sep 25, 2012
Author:  Justin Rich (justin.rich@gi.alaska.edu)
Location: Geophysical Institute | University of Alaska, Fairbanks
Contributors:

Copyright:   (c) Justin L. Rich 2012
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
import arcpy as ARCPY                                        #@UnresolvedImport

class column ():
    
    def __init__ (self, input_file, position, new_column_name, new_column_type, new_column_precision = '', new_column_scale = '', new_column_length = '', new_column_alias = '', new_column_nullable = '', new_column_required = '', new_column_domain = ''):
        
        try: import arcinfo #Get ArcInfo License - @UnresolvedImport@UnusedImport
        except: print 'ArcInfo license NOT available'

        try: # Check out Spatial Analyst extension if available.
            if ARCPY.CheckExtension('Spatial') == 'Available':
                ARCPY.CheckOutExtension('Spatial')
        except: print 'Spatial Analyst extension not available'
        
        # Get list of existing fields in the shapefile given
        column_list = ARCPY.ListFields(input_file)
        # Flip the position so that it can be based from the front of the table
        # and subtract one to place it at the actual position given (table starts
        # at zero not one).
        position = (len(column_list)-position)+1
        
        try:
            self.insert_column(input_file, column_list, position, new_column_name, new_column_type, new_column_precision, new_column_scale, new_column_length, new_column_alias, new_column_nullable, new_column_required, new_column_domain) # Insert new column
            print 'INSERT COMPLETE'
        except: print 'INSERT FAILED'
        
        
    def insert_column (self, input_file, column_list, position, new_column_name, new_column_type, new_column_precision, new_column_scale, new_column_length, new_column_alias, new_column_nullable, new_column_required, new_column_domain):
        """Recursive to parse the list of columns in a shapefile and insert
        a new column at the position given."""
        
        def callback_shuffle (shapefile, col):
            """Callback: Shuffles data in a column to the end of the table."""
            # Add a temporary field to the table an copy data from the target
            # column to it. Then delete original field
            ARCPY.AddField_management(shapefile, "TMP", col.type, col.precision, col.scale, col.length, col.aliasName, col.isNullable, col.required, col.domain)
            ARCPY.CalculateField_management(shapefile, 'TMP', "!"+col.name+"!", 'PYTHON', '')
            ARCPY.DeleteField_management (shapefile, col.name) # Drop the original field
            
            # Add a new field, named same as the one just deleted, to the table, 
            # copy the data stored in the temp field to it and delete the temp field
            ARCPY.AddField_management(shapefile, col.name, col.type, col.precision, col.scale, col.length, col.aliasName, col.isNullable, col.required, col.domain)
            ARCPY.CalculateField_management(shapefile, col.name, "!TMP!", 'PYTHON', '')
            ARCPY.DeleteField_management (shapefile, 'TMP') # Drop the temp field
            
        # Recursive termination condition
        if len(column_list) == 0:
            return "Insert Column Complete"
        else:
            # If the position has not be reached, pop the next column
            if len(column_list) > position: 
                column = column_list.pop(0) # Pop the next column in the list

            # If the position is reached add the new field
            elif len(column_list) == position:
                ARCPY.AddField_management(input_file, new_column_name, new_column_type, new_column_precision, new_column_scale, new_column_length, new_column_alias, new_column_nullable, new_column_required, new_column_domain)
                
                column = column_list.pop(0) # Pop the next column in the list
                callback_shuffle (input_file, column) # Shuffle popped column

            # After the position has been reached just pop and shuffle
            elif len(column_list) < position:
                column = column_list.pop(0) # Pop the next column in the list
                callback_shuffle (input_file, column) # Shuffle popped column
                
        # Pass the new column list and re-run insert_column. This is done until
        # the termination condition is met (column list is empty) 
        return self.insert_column(input_file, column_list, position, new_column_name, new_column_type, new_column_precision, new_column_scale, new_column_length, new_column_alias, new_column_nullable, new_column_required, new_column_domain)


#_______________________________________________________________________________
#***  DRIVER *******************************************************************
# HARD CODE INPUTS HERE !
def driver():
    # Required Fields
    input_file = r'A:\Desktop\PostgreSQL\Alaska_Modern.shp'
    new_column_name = r'BGNDATE'
    new_column_type = r'DATE'
    position = 6 # Must be greater then 2 (1 = 'FID' & 2 = 'Shape')
    
    # Optional Fields
    new_column_precision = ''
    new_column_scale = ''
    new_column_length = ''
    new_column_alias = ''
    new_column_nullable = ''
    new_column_required = ''
    new_column_domain = ''


    column (input_file, position, new_column_name, new_column_type, new_column_precision, new_column_scale, new_column_length, new_column_alias, new_column_nullable, new_column_required, new_column_domain)

if __name__ == '__main__':
    driver()