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

def las_resample (input_folder, output_folder, snap, cell_size):
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
    
    
def relabel_lasshp (input_folder, output_folder):
    """ The function reads in the las shapefile generated in 
    las_resample and reformats it with name, day and year in
    the attribute table."""
    envi = environment.setup_arcgis (output_folder, False, False)
    workspace = envi._workspace
    arcpy = envi._arcpy
    
    for shapefile in glob.glob (os.path.join (input_folder, '*.shp')):
            
        name = os.path.basename(shapefile)
        glacier = name.split('_')[0]
        year = name.split('_')[1]
        day  = name.split('_')[2][0:3]
        
        print name, glacier, year, day
    
        try:
            # Process: Add Fields
            lidar = arcpy.CreateFeatureclass_management(workspace, name, 'POINT', '', '', '', projection.alaska_albers())
             
            fields = (('NAME', 'STRING'), ('GLIMSID', 'STRING'), ('YEAR', 'INTEGER'), ('DAY', 'INTEGER'), ('X', 'LONG'), ('Y', 'LONG'), ('Z', 'DOUBLE'))
            for field in fields: arcpy.AddField_management(lidar, field[0], field[1])
            arcpy.DeleteField_management(lidar, 'ID')
        
            rows = arcpy.InsertCursor(lidar, projection.alaska_albers())
        
            points = arcpy.SearchCursor(shapefile)
            for point in points:
                
                row = rows.newRow()
                row.setValue("Shape", point.Shape)
                row.setValue("NAME", glacier)
                # GLIMS ID GOES HERE - us 'lasshp_spatial' join
                row.setValue("YEAR", year)
                row.setValue("DAY", day)
                row.setValue("X", point.X)
                row.setValue("Y", point.Y)
                row.setValue("Z", point.Z)
                
                rows.insertRow(row)
                
            del point, points, rows
        except:
            print '    Failed: ', glacier, year, day



def lasshp_spatialjoin (input_folder, output_folder, glaciers):
    """ This function reads in las shapefiles and spatially joins the
    to glacier outlines. The purpose is to get the glims id"""
    glacier_list = []

    # Setup workspace
    envi = environment.setup_arcgis (False, False, False)
    arcpy = envi._arcpy
                
    for shapefile in glob.glob (os.path.join (input_folder, '*.shp')):
            
        name = os.path.basename(shapefile)
        glacier = name.split('_')[0]
        year = name.split('_')[1]
        day  = name.split('_')[2][0:3]
        
        if name not in glacier_list:
            print glacier, year, day
    
            output = output_folder + '\\' + name
            arcpy.SpatialJoin_analysis(shapefile, glaciers, output)
             
            arcpy.CalculateField_management(output, 'GLIMSID', '!GLIMSID_1!', 'PYTHON')
             
            drop_list = ['Join_Count', 'TARGET_FID', 'RGIID', 'GLIMSID_1', 'RGIFLAG', 'BGNDATE', 'ENDDATE', 'CENLON', 'CENLAT', 'O1REGION', 'O2REGION', 'AREA', 'GLACTYPE', 'NAME_1', 'PARK', 'MIN', 'AVG', 'MAX']
            for item in drop_list:
                arcpy.DeleteField_management(output, item)
                

def las_shape_csv (input_folder, output_folder):
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
        
        output_name = output_folder + '\\' + '%s_%s_%s.csv' %(glacier, year, day)
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
    input_folder = r'A:\Desktop\New folder\Reformate\scratch'
    output_folder = r'A:\Desktop\New folder\Join'
    glacier = r'A:\Desktop\PostgreSQL\Alaska_Modern.shp'
    
#     las_resample (input_folder, output_folder, snap, cell_size)
    lasshp_spatialjoin (input_folder, output_folder, glacier)
if __name__ == '__main__':
    driver ()        
