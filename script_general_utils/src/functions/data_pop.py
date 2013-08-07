"""****************************************************************************
 Name:         glacier_utilities.functions.data_pop
 Purpose:     
 
Created:         Nov 19, 2012
Author:          Justin Rich (justin.rich@gi.alaska.edu)
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
import arcpy                                       

def generate_GLIMSIDs (input_file, workspace):
    """Generate GLIMS id's for the input table. These are based on latitude
    and longitude. File is re-projected into WGS84 to obtain these. 
    WARNING - ID's checked for Alaska but have NOT YET been verified in 
    other regions."""
    # Create a copy of the input in WGS 84 for calculating Lat. / Lon.
    from utilities.projection import wgs_84
    
    output_wgs84 = workspace + "\\Input_File_WGS84.shp"
    arcpy.Project_management(input_file, output_wgs84, wgs_84())
    
    glims_values = [] # Hold the ID's to add to non WGS-84 Table
    rows = arcpy.UpdateCursor(output_wgs84)
    for row in rows:
        #Find the Centroid Point
        featureCenter = row.getValue(arcpy.Describe(output_wgs84).shapeFieldName)
        X = int(round(featureCenter.centroid.X, 3) * 1000) # Get X of Centroid
        Y = int(round(featureCenter.centroid.Y, 3) * 1000) # Get Y of Centroid
    
        # Format the E and N/S values appropriately. 
        if X < 0: X = str((360000 + X) ) + "E"      # Values 180-360
        else: X = str(X) + "E" # Values Greater then or equal to 100
        # Account for values that are not long enough (i.e. 0.0025 would otherwise be 25)
        X = (7 - len(X)) * '0' + X

        if Y < 0: Y = str(-1 * Y) + "S"     # Values to the south
        else: Y = str(Y) + "N" # Values to the north
        Y = (6 - len(Y)) * '0' + Y # Account for values that are not long enough 
       
        glims_values.append("G"+ str(X) + str(Y)) # Append value to list of values
    
    arcpy.Delete_management(output_wgs84) # Delete temporary re-projected file
    del row, rows     #Delete cursors and remove locks
    
    # Get ID count to return. i.e. number of glaciers
    id_count = str(len(glims_values))
    
    # Transfer calculated GLIMS IDs to the original input file
    rows = arcpy.UpdateCursor (input_file)
    for row in rows:
        row.GLIMSID = glims_values.pop(0) # pop next value and print it to file.
        rows.updateRow(row) # Update the new entry
    del row, rows #Delete cursors and remove locks
    return id_count # Return number of IDs generated


def generate_RGIIDs (input_file, version, region):
    """Generate RGI id's for the input table. This requires including the version
    and region numbers as input values."""
    id_count = 0
    rgi_starter = 'RGI' + str(version) + '-' + str(region) + '.'
    
    rows = arcpy.UpdateCursor (input_file)
    for row in rows:
        row_value = row.FID + 1
        try:
            if row_value < 10: row.RGIID = rgi_starter + '0000' + str(row_value)
            if row_value >= 10 and row_value < 100: row.RGIID = rgi_starter + '000' + str(row_value)
            if row_value >= 100 and row_value < 1000: row.RGIID = rgi_starter + '00' + str(row_value)
            if row_value >= 1000 and row_value < 10000: row.RGIID = rgi_starter + '0' + str(row_value)
            if row_value >= 10000 and row_value < 100000: row.RGIID = rgi_starter + '' + str(row_value)
            rows.updateRow(row) # Update the new entry
        except: pass
        id_count += 1
    del row, rows #Delete cursors and remove locks
    del row_value, rgi_starter # Delete variables not need
    return str(id_count)




def auto_generate_RGIIDs (input_file, version):
    """Generate RGI ID's automatically. This function uses the 'Gennerate
    RGIIDs' function and is made to simply parse out the region number."""
    rows = arcpy.SearchCursor(input_file)
    for row in rows:
        region_number = str(row.getValue('O1REGION'))
        break
    del row, rows
    
    if len(region_number) == 1: 
        region_number = '0' + region_number
    
    generate_RGIIDs (input_file, version, region_number)
    return True


def generate_centroid (input_file):
    """Generate RGI Glacier Centroids. Requires the data to be in a geographic
    projection and both a 'CENLON' and 'CENLAT' field."""
    rows = arcpy.UpdateCursor(input_file)
    for row in rows:
        #Find the Centroid Point
        featureCenter = row.getValue(arcpy.Describe(input_file).shapeFieldName)
        row.setValue('CENLON', featureCenter.centroid.X)
        row.setValue('CENLAT', featureCenter.centroid.Y)
        
        rows.updateRow(row) # Update the new entry
    del row, rows
    return True


def driver():
    print 'STARTING'
    input_file = r'A:\Desktop\RGI32\RGI32RAW\01_rgi32_Alaska.shp'
    generate_centroid(input_file)
    print 'FINISHED'

if __name__ == '__main__':
    driver()


