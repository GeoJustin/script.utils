"""****************************************************************************
 Name:         hypsometry
 Purpose:     
 
Created:         Aug 16, 2013
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
import math
import functions.data_calc as DC
import utilities.environment as environment
import utilities.projection as projection


def hypsometry (self, shapefile, DEM, output_folder, snap, min_bin = 0, max_bin = 8850, bin_size = 50, buffer_scale = 2):
    """This function takes in a shapefile of glacier extents and produces a 
    new shapefile with glacier extents broken down into individual bins. """
    
    envi = environment.setup_arcgis (output_folder, True, True)
    scratch = envi._workspace
    arcpy = envi._arcpy
    spatial = envi._spatial
    log = envi._log
    
    arcpy.env.snapRaster = snap
    
    # Generate re-map string for the reclassify function. This done by first
    # calculating the number of bins and then finding the low and high values
    # for each bin and then giving it a label
    reclassify_range = '' # re-map string
    total_bins = round(math.ceil(float(max_bin - min_bin) / float(bin_size)), 0)
    for bin_num in range (0, int(total_bins)):  # For each bin...
        low_value =  bin_num * bin_size         # Low value in range and re-map value
        high = float((bin_num + 1) * bin_size)  # High value in range
        reclassify_range += str(float(low_value)) + " " + str(high) + " " + str(low_value) + ";"
        
    # Create new shapefile to send bins to
    new_feature = arcpy.CreateFeatureclass_management(output_folder, 'Merged_Binned.shp', 'POLYGON', '', '', '', projection.alaska_albers())
    arcpy.AddField_management(new_feature, 'GLIMSID', 'STRING', '', '', 14)
    arcpy.AddField_management(new_feature, 'ELEVATION', 'STRING')
    
    count = 0
    glaciers = arcpy.SearchCursor(shapefile) # Open shapefile to read features
    for glacier in glaciers: # For each feature in the shapefile
        
        count += 1
    
        try:
            print '%s - Working on %s - %s km2' %(count, glacier.GLIMSID, glacier.AREA)
            subset = scratch + '\\' + 'raster_subset_' + str(glacier.GLIMSID) + '.img'
        
            # Subset the DEM based on a single buffered glacier outline
            # Buffer the input features geometry
            cellsize = float(DC.get_properties(DEM, 'CELLSIZEX')) * buffer_scale
            mask = arcpy.Buffer_analysis(glacier.shape, arcpy.Geometry(), cellsize)
            
            # Extract by mask using the buffered feature geometry
            extract = spatial.ExtractByMask (DEM, mask[0])
            extract.save(subset) # Save extracted mask as subset
            
            # Reclassify the DEM based on bins
            reclassify =  scratch + '\\' + 'Reclassify_Raster_' + str(glacier.GLIMSID) + '.img'
            reclass_raster = spatial.Reclassify (subset, "Value", reclassify_range, "NODATA")
            reclass_raster.save(reclassify)
            
            # Create a clipped feature from the input raster.  
            # Scale the subset DEM and temporarily save it to file. If it is not
            # saved an error is sometimes thrown when converting to polygon.
            # This is no good reason for this VAT error.
            raster_scaling = 1000
            subset_name = scratch + '\\raster_to_poly.img'
            subset_ints = spatial.Int(spatial.Raster(reclassify) * raster_scaling + 0.5)
            subset_ints.save(subset_name)
        
            polygon = arcpy.RasterToPolygon_conversion(subset_ints, subset_name, "NO_SIMPLIFY")
           
            feature_name = scratch + '\\' + 'binned_' + glacier.GLIMSID + '.shp'
            clipped = arcpy.Clip_analysis(polygon, glacier.shape, feature_name)
        
        
            rows = arcpy.InsertCursor(new_feature, projection.alaska_albers())    
            bins = arcpy.SearchCursor(clipped)
            for ebin in bins:
                row = rows.newRow()
                row.setValue("Shape", ebin.Shape)
                row.setValue("GLIMSID", glacier.GLIMSID)
                row.setValue("ELEVATION", ebin.GRIDCODE)
                rows.insertRow(row)
            del bins, ebin, rows
        
            envi.delete_items([subset, mask, extract, reclassify, subset_name, subset_ints, polygon, clipped])
                    
        except: log.print_line(str(row.GLIMSID) + ' -     ERROR - Could not generate hypsometry')  
        
    envi.remove_workspace()
    log.print_line('Finished')
        
        
        
        
def hypsometry_csv (self, shapefile, output):
    """This function takes in the hypsometry file generated from the 'hypsometry'
    function and reads it into a csv file."""
    envi = environment.setup_arcgis (False, False, False)
    arcpy = envi._arcpy


    def dictionary (max_bin = 8850, min_bin = 0, bin_size = 50):
        """Generate a default dictionary calculated here from minimum elevation, 
        maximum elevation and bin size. A ceiling function is used to ensure that 
        the number of bins is inclusive and rounded to produce an integer."""
        bins = {}
        total_bins = round(math.ceil(float(max_bin - min_bin) / float(bin_size)), 0)
        for count in range (0, int(total_bins)):      
            bins[min_bin + (count * bin_size)] = 0                 
        return bins 
        
    
    glaciers = {} 
    rows = arcpy.SearchCursor(shapefile)
    for row in rows: 
        if row.GLIMSID not in glaciers:
            glaciers[row.GLIMSID] = dictionary()
        glaciers[row.GLIMSID][row.ELEVATION] += row.AREA
    del row, rows
    
    
    output = open (output, 'w')
    output.write('GLIMSID, ' + 'BIN, '.join([str(heading) for heading in sorted(dictionary().iterkeys())]) + '\n')
    
    for key, values in glaciers.iteritems():
        line = key
        while len(values) > 0: 
            line += ', %s' %(values.pop(min(values)))
        line += '\n'
        output.write(line)
        
    output.close()


            
def driver ():
    
    shapefile = r'A:\Desktop\Alaska\Glaciers_Mapdate.shp'
    dem = r'A:\Desktop\Alaska\NED_ALB.img'
    output = r'A:\Desktop\Alaska\Development'
    
    snap = r'A:\Desktop\DatabaseImport\SnapRaster\SnapRaster.img'
    
    hypsometry(shapefile, dem, output, snap)
    
    pass
if __name__ == '__main__':
    driver ()        
