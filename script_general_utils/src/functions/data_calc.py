"""****************************************************************************
 Name: functions_data_calc
 Purpose: The purpose of this module is to hold basic  functions 
     that deal with calculation of statistics including slope and aspect 
     information as well as function for basic operations such as sub-setting 
     a DEM or converting a raster to a feature.
 
Created: Oct 12, 2012
Author:  Justin Rich (justin.rich@gi.alaska.edu)
Location: Geophysical Institute | University of Alaska, Fairbanks
Contributors: Christian Kienholz, University of Alaska, Fairbanks

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
import os
import math
import arcpy                                                #@UnresolvedImport
from arcpy import sa as spatial


def calc_length (feature, length_field = 'LENGTH'):
    """Calculate the length of a line segment. This function calculates 
    to a field called 'LENGTH' unless otherwise specified and calculates a 
    value to it."""
    # Check to see if there is a length field to use. 
    if arcpy.ListFields(feature, 'LENGTH'):  arcpy.AddField_management(feature, length_field, 'DOUBLE')
    arcpy.CalculateField_management(feature, length_field, 'float(!shape.length@meters!)', 'PYTHON')


def get_fields (feature, required = False):
    """Identifies and returns a list of field headers for a feature class.
    If required is False, only none required fields (i.e. FID, Shape) will be returned"""
    if required == True: fields = [fields.name for fields in arcpy.ListFields(feature)]
    if required == False: fields = [fields.name for fields in arcpy.ListFields(feature) if fields.name <> 'FID' and fields.name <> 'Shape']
    return fields 
       
       
def get_bin_statistic (feature, bin_mask, statistic = 'MIN'):
    """Returns basic bin statistics given the geometry of a second feature.
    This function was designed to work on bin_mask files generated form the 
    bin by dem function."""
    bins = list()
    
    selection = 'Selection'
    arcpy.MakeFeatureLayer_management(bin_mask, selection)
    arcpy.SelectLayerByLocation_management(selection, 'INTERSECT', feature) 
        
    rows = arcpy.SearchCursor(selection)
    for row in rows: 
        bins.append(row.BINS)
    del row, rows
    
    arcpy.Delete_management(selection)
        
    if statistic == 'MIN': return min(bins)
    if statistic == 'MAX': return max(bins)
    if statistic == 'NUM': return len(bins)
    if statistic == 'VAL': return bins
    else: pass


def calc_slope (feature, bin_mask, bin_size = 50, sort_by = 'BINS'):
    """Calculate slope information along the center line by clipping segments of the 
    centerline to each bin. A bin mask is required and is calculated as a standard
    output of the 'get_hypsometry' function. Slope calculations assume centerline 
    segment runs the length of the bins so first and last values may be incorrect if
    if the line end before it reaches the end of a bin or starts within it."""
    feature_list = list()

    selection = 'Selection'
    arcpy.MakeFeatureLayer_management(bin_mask, selection)
    arcpy.SelectLayerByLocation_management(selection, 'INTERSECT', feature) 
    
    cum_length = 0
    rows = arcpy.SearchCursor(selection, '', '', '', sort_fields='%s A;' %(sort_by))
    for row in rows: 
        
        clipped_line = arcpy.Clip_analysis (feature, row.shape, 'in_memory\\clipped_line')
        for length in arcpy.SearchCursor (clipped_line):
            
            geometry = length.Shape
            line_len = length.Shape.length
            cum_length += line_len
            slope = round(math.degrees(math.atan(bin_size / line_len)), 1)
            
            feature_list.append((geometry, line_len, cum_length, slope))

        arcpy.Delete_management(clipped_line)
    del row, rows
    
    arcpy.Delete_management(selection)
    return feature_list
    
    


def bin_by_dem (feature, dem, scratch, name = None, bin_size = 50):
    """Calculate bins  from the given digital elevation model
    (DEM) and return bin statistics."""
    # Build Export Name. This option is largely included in case there is unexpected 
    # naming conflicts with other functions
    if name == '' or name == None: name = os.path.join(scratch,'Binned.shp')
    else: name = os.path.join(scratch, name)
    
    min_bin = 0 # Force default min_bin to sea level. DO NOT CHANGE. 
    max_bin = 8850
    
    reclassify_range = '' # re-map string
    # Generate re-map string for the reclassify function. This done by first
    # calculating the number of bins and then finding the low and high values
    # for each bin and then giving it a label.
    total_bins = round(math.ceil(float(max_bin - min_bin) / float(bin_size)), 0)
    for bin_num in range (0, int(total_bins)):  # For each bin...
        low_value =  bin_num * bin_size         # Low value in range and re-map value
        high_value = (bin_num + 1) * bin_size  # High value in range
        reclassify_range += str(float(low_value)) + " " + str(float(high_value)) + " " + str(low_value) + ";"

    # Reclassify the DEM based on bins
    filled = spatial.Fill (dem) # Fill DEM
    reclass_raster = spatial.Reclassify (filled, "Value", reclassify_range, "NODATA")

    # Create a clipped feature from the input raster.
    poly_raster = raster_to_polygon (feature, reclass_raster, scratch, '', 1)
    
    # Clip and clean to the original input feature
    arcpy.Clip_analysis (poly_raster, feature,  name)
    
    # Format output table.
    to_delete = get_fields(name)
    fields = [('BINS', 'INTEGER', "'!grid_code!'"), ('STEP_SIZE', 'INTEGER', bin_size)]
    for field in fields: 
        arcpy.AddField_management(name, field[0], field[1])
        arcpy.CalculateField_management(name, field[0], field[2], 'PYTHON')
    for item in to_delete: arcpy.DeleteField_management(name, item)
    
    arcpy.Delete_management(filled)
    arcpy.Delete_management(poly_raster)
    return name



def get_properties (raster, prop = ''):
    """Return the desired property from the input raster layer. These include:
    MINIMUM, MAXIMUM, MEAN, STD, ... etc."""
    return str(arcpy.GetRasterProperties_management(raster, prop))
       
        

def subset (feature, raster, scratch, name = None, buffer_scale = 2):
    """Subset a raster based on an input features boundaries plus a buffer
    which should be greater then the size of the pixels in the given raster.
    This is to ensure there are no gaps between where the raster ends and the
    input feature begins. Any excess raster will be clipped later after it is
    converted to a feature class."""
    # Build Export Name. This option is largely included in case there is unexpected 
    # naming conflicts with other functions
    if name == '' or name == None: subset = os.path.join(scratch,'Subset.img')
    else: subset = os.path.join(scratch, name)
    
    # Buffer the input features geometry
    cellsize = float(get_properties(raster, 'CELLSIZEX')) * buffer_scale
    mask = arcpy.Buffer_analysis(feature, arcpy.Geometry(), cellsize)
    
    # Extract by mask using the buffered feature geometry
    extract = spatial.ExtractByMask (raster, mask[0])
    extract.save(subset) # Save extracted mask as subset
    
    arcpy.Delete_management(mask)
    del cellsize
    
    return subset

    
def raster_to_polygon (feature, raster, scratch, name = None, raster_scaling = 1000):
    """Convert raster to a features class, clip it to an input feature and
    calculate the area of each polygon. This new feature class is then 
    returned for calculating statistics. """
    # Build Export Name. This option is largely included in case there is unexpected 
    # naming conflicts with other functions
    if name == '' or name == None: polygon = os.path.join(scratch,'Raster_to_Polygon.shp')
    else: polygon = os.path.join(scratch, name)
    
    # Scale the subset DEM and temporarily save it to file. If it is not
    # saved, a VAT error is sometimes thrown when converting to polygon.
    subset = spatial.Int(raster * raster_scaling)

    converted = arcpy.RasterToPolygon_conversion(subset, 'in_memory\\rtp_result', 'NO_SIMPLIFY')
    arcpy.Clip_analysis(converted, feature, polygon)
    
    arcpy.Delete_management(subset)
    arcpy.Delete_management(converted)

    return polygon
    
    