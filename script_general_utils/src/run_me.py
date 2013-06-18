"""****************************************************************************
 Name:         run_me
 Purpose:      Used to run scripts that make use of the utils package. This 
     script is not intended to be permanent.
 
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
bin_size = 100

envi = utilities.environment.setup_arcgis (workspace, True, True)
scratch = envi._workspace
log = envi._log
arcpy = envi._arcpy

centerlines = workspace + '\\Centerlines.shp'
arcpy.CopyFeatures_management(input_centerlines, centerlines)

fields = (('LINEID', 'STRING'), ('LENGTH', 'DOUBLE'), ('CUMMLENGTH', 'DOUBLE'), 
          ('TOTLENGTH', 'DOUBLE'), ('ZEROLENGTH', 'DOUBLE'), ('SLOPE', 'DOUBLE'),
          ('MAINLENGTH', 'DOUBLE'))
polylinefeature = arcpy.CreateFeatureclass_management(workspace, 'New_Centerlines.shp', 'POLYLINE', '', '', '', centerlines)
for field in fields: 
    arcpy.AddField_management(polylinefeature, field[0], field[1])
arcpy.DeleteField_management(polylinefeature, 'ID')

main_length = {}
search_main = arcpy.SearchCursor(centerlines)
for search in search_main:
    if search.MAIN == 1:
        main_length [search.GLIMSID] = search.LENGTH
        
glacier_id = ''
binned_glacier = ''

search_rows = arcpy.SearchCursor(centerlines)
for search_row in search_rows:
    if search_row.GLIMSID <> glacier_id:
        
        print 'Extracting BINS from: ', search_row.GLIMSID
        glacier_id = search_row.GLIMSID
        
            # Select Feature by GLIMS ID
        feature_layer = 'Feature_Layer'
        arcpy.MakeFeatureLayer_management(boundaries, feature_layer)
        arcpy.SelectLayerByAttribute_management(feature_layer, 'NEW_SELECTION', """ "GLIMSID" = '%s' """ %(glacier_id) )
                
        # Subset DEM by Selected Feature
        subset = dc.subset(feature_layer, dem, scratch)
        
        # Create Bins from Subset and Feature
        binned_glacier = dc.bin_by_dem(feature_layer, subset, scratch, 'Binned_%s.shp'%(glacier_id), bin_size)
        
        # Delete Subset, Selection Layer, ...etc.
        envi.delete_items([feature_layer, subset])

        
    print  '\tRunning - ', search_row.GLIMSID
    slope_bins = dc.calc_slope(search_row.shape, binned_glacier, bin_size)
    
    rows = arcpy.InsertCursor(polylinefeature)
    for item in slope_bins:
        row = rows.newRow()
        row.setValue("Shape", item[0])
        row.setValue("LINEID", search_row.GLIMSID)
        row.setValue("LENGTH", item[1])
        row.setValue("CUMMLENGTH", item[2])
        row.setValue("TOTLENGTH", search_row.shape.length)
        row.setValue("ZEROLENGTH", search_row.LENGTH)
        row.setValue("MAINLENGTH", main_length[glacier_id])
        row.setValue("SLOPE", item[3])
        rows.insertRow(row)
    del row, rows
    
del search_row, search_rows
# envi.remove_workspace()




