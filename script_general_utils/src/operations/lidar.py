"""****************************************************************************
 Name:         operations.resample_las
 Purpose:     
 
Created:         Aug 29, 2013
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
import os
import glob
import utilities.environment as environment
import utilities.projection as projection

def las_resample (self, input_folder, output_folder, snap, cell_size):
    """This function reads in las files from a folder and averages the per
    grid cell, based on an input snap raster, and outputs the cell center
    as a shapefile. This function was designed to work on an Alaska Albers
    grid and it is recommended that the input snap raster have 0,0 as it's 
    origin point."""
    
    envi = environment.setup_arcgis (output_folder, True, True)
    arcpy = envi._arcpy
    log = envi._log
    
    arcpy.env.outputCoordinateSystem = projection.alaska_albers()
    arcpy.env.cellSize = cell_size
    arcpy.env.snapRaster = snap
    
    for las in glob.glob (os.path.join (input_folder, '*.las')):
        name = os.path.basename(las)
        glacier = name.split('.')[0]
        year = name.split('.')[1]
        day  = name.split('.')[2]
    
        log.print_line('Starting: %s,  %s,  %s' %(glacier, year, day))

        las_dataset = 'las.lasd'
        arcpy.CreateLasDataset_management(las, las_dataset)

        las_Layer = 'las_Layer'
        arcpy.MakeLasDatasetLayer_management (las_dataset, las_Layer)
       
        las_raster = 'Las_raster.img'
        arcpy.LasDatasetToRaster_conversion(las_Layer, las_raster, "ELEVATION", "BINNING AVERAGE NONE", "FLOAT", "CELLSIZE", cell_size, "1")
    
        points = output_folder + '\\' + '%s_%s_%s.shp' %(glacier, year, day)
        arcpy.RasterToPoint_conversion(las_raster, points, 'VALUE')
        
        # Process: Add Fields
        fields = (('X', 'DOUBLE'), ('Y', 'DOUBLE'), ('Z', 'DOUBLE'))
        for field in fields:
            arcpy.AddField_management(points, field[0], field[1])
        arcpy.DeleteField_management(points, 'POINTID')
    
        # Process: Calculate Fields
        desc = arcpy.Describe(points).shapeFieldName
        rows = arcpy.UpdateCursor (points)
        for row in rows:
            featureCenter = row.getValue(desc)
            row.setValue('X', featureCenter.centroid.X)
            row.setValue('Y', featureCenter.centroid.Y)
            row.setValue('Z', row.getValue('GRID_CODE'))
            rows.updateRow(row)
        del row, rows
        
        arcpy.DeleteField_management(points, 'GRID_CODE')
       
        envi.delete_items([las_dataset, las_Layer, las_raster])
    envi.remove_workspace()



def las_shape_csv (self, input_folder, output_folder):
    """This function reads in every shapefile in a given folder and writes
    them into a csv file in a format useful to database import."""
    envi = environment.setup_arcgis (output_folder, False, False)
    arcpy = envi._arcpy
    log = envi._log
    
    # Run each shapefile in the folder
    for shapefile in glob.glob (os.path.join (input_folder, '*.shp')):
        name = os.path.basename(shapefile)
        glacier = name.split('_')[0]
        year = name.split('_')[1]
        day  = name.split('_')[2][0:3]
    
        log.print_line("%s - %s - %s" %(glacier, year, day))
        
        output_name = output_folder + '\\' + '%s_%s_%s.shp' %(glacier, year, day)
        output = open (output_name, 'w')
    
        rows = arcpy.SearchCursor(shapefile) # Load each point into the csv file
        for row in rows:
            x = int(row.getValue('X'))
            y = int(row.getValue('Y'))
            z = row.getValue('Z')
            output.write(",".join([glacier, str(year), str(day), str(int(x)), str(int(y)), str(z)]) + '\n')
        del row, rows
        
        output.close()
    envi.remove_workspace()   



def driver ():
    input_folder = r'A:\Desktop\DatabaseImport\LiDAR_RunSpecial'
    output_folder = r'A:\Desktop\DatabaseImport\Resampled_10'

    snap = r'A:\Desktop\DatabaseImport\SnapRaster\SnapRaster.img'
    cell_size = 10
    
    las_resample (input_folder, output_folder, snap, cell_size)
if __name__ == '__main__':
    driver ()        
