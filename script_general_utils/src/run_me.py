"""****************************************************************************
 Name:         run_me
 Purpose:     
 
Created:         Jun 5, 2013
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
import utilities.environment
import functions.data_calc as dc

input_centerlines = r'A:\Desktop\Justin_Glacierbay_prelim\Data\BRANCHES.shp'
boundaries = r'A:\Desktop\Justin_Glacierbay_prelim\Data\glacieroutlines.shp'
workspace = r'A:\Desktop\Justin_Glacierbay_prelim\Scratch'
dem = r'V:\DEM\NewDEM_V2\Alaska_albers_V2.tif'
bin_size = 30

envi = utilities.environment.setup_arcgis (workspace, True, True)
scratch = envi._workspace
arcpy = envi._arcpy

centerlines = workspace + '\\Centerlines.shp'
arcpy.CopyFeatures_management(input_centerlines, centerlines)
arcpy.AddField_management(input_centerlines, 'BIN_START', 'INTEGER')
arcpy.AddField_management(input_centerlines, 'BIN_STEP', 'INTEGER')
arcpy.AddField_management(input_centerlines, 'BIN_SLOPE', 'TEXT')




def get_bin (glacier_id):
    # Select Feature by GLIMS ID
    feature_layer = 'Feature_Layer'
    arcpy.MakeFeatureLayer_management(boundaries, feature_layer)
    arcpy.SelectLayerByAttribute_management(feature_layer, 'NEW_SELECTION', """ "GLIMSID" = '%s' """ %(glacier_id) )
            
    # Subset DEM by Selected Feature
    subset = dc.subset(feature_layer, dem, scratch)
    
    # Create Bins from Subset and Feature
    binned_glacier = dc.bin_by_dem(feature_layer, subset, scratch, '', bin_size)
    
    # Delete Subset, Selection Layer, ...etc.
    envi.delete_items([feature_layer, subset])
    
    return binned_glacier # Return Bins





def calc_centerline_info (feature, bin_mask):
    
    print dc.get_bin_statistic(feature.shape, bin_mask, 'MIN'),
    print dc.get_bin_statistic(feature.shape, bin_mask, 'MAX'),
    print dc.get_bin_statistic(feature.shape, bin_mask, 'NUM'),
    print bin_size
    
            
    feature.BIN_START = dc.get_bin_statistic(feature.shape, binned_glacier, 'MIN')
    feature.BIN_STEP = bin_size
    
    slope_bins = dc.calc_slope(feature.shape, bin_mask, bin_size)
    print 'Length', slope_bins
    feature.BIN_SLOPE = str(slope_bins)



glacier_id = ''
binned_glacier = ''

rows = arcpy.UpdateCursor(centerlines)
for row in rows:
    if row.GLIMSID == glacier_id:
        print  'Same - ', row.GLIMSID
        
        calc_centerline_info (row, binned_glacier)

        
        rows.updateRow(row)
    else:
        print row.GLIMSID
        
        try: arcpy.Delete_management(binned_glacier) # Try will fail on first (empty)
        except: pass
        
        glacier_id = row.GLIMSID
        binned_glacier = get_bin (glacier_id)
    
        calc_centerline_info (row, binned_glacier)
    
del row, rows
envi.remove_workspace()