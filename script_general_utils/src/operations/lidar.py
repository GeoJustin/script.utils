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
    

def profile_shapefile (input_folder, output_folder, glaciers, snap, cell_size):
    """ This function takes in prifiler data (text file) from a folder and 
    averages the per grid cell, based on an input snap raster, and outputs 
    the cell center as a shapefile. This function was designed to work on 
    an Alaska Albers grid and it is recommended that the input snap raster 
    have 0,0 as it's origin point."""
    envi = environment.setup_arcgis (output_folder, True, True)
    workspace = envi._workspace
    arcpy = envi._arcpy
    log = envi._log
    
    arcpy.env.outputCoordinateSystem = projection.alaska_albers()
    arcpy.env.cellSize = cell_size
    arcpy.env.snapRaster = snap
    
    for utm in glob.glob (os.path.join (input_folder, '*.utm*')):
        name = os.path.basename(utm)
        glacier = name.split('.')[0]
        year = name.split('.')[1]
        day  = name.split('.')[2]
        ident = name.split('.')[3]
        zone = name.split('.')[4]
        
        log.print_line('Starting: %s,  %s,  %s, %s' %(glacier, year, day, zone))
        
        proj = {'utm4': projection.wgs_84_utm4n(), 'utm5': projection.wgs_84_utm5n(), 'utm6': projection.wgs_84_utm6n(), 'utm7': projection.wgs_84_utm7n(), 'utm8': projection.wgs_84_utm8n(), 'utm9': projection.wgs_84_utm9n()}
        name = '%s_%s_%s_%s.shp' %(glacier, year, day, ident)
        profile = arcpy.CreateFeatureclass_management(workspace, name, 'POINT', '', '', '', proj[zone])
        
        fields = (('X', 'LONG'), ('Y', 'LONG'), ('Z', 'DOUBLE'))
        for field in fields: arcpy.AddField_management(profile, field[0], field[1])
        arcpy.DeleteField_management(profile, 'ID')
        
        rows = arcpy.InsertCursor(profile)
        
        read = open (utm, 'r')
        header = [read.readline() for line in range(0, 11)]  # @UnusedVariable
        for line in read:
            E = line.split()[9]
            N = line.split()[10]
            Z = line.split()[11] 
    
            row = rows.newRow()
            row.setValue("Shape", arcpy.PointGeometry(arcpy.Point(E, N)))
            row.setValue("Z", Z)
            rows.insertRow(row)
        del row, rows
        
        projected = '%s_%s_%s_%s_Albers.shp' %(glacier, year, day, ident)
        arcpy.Project_management (profile, projected, projection.alaska_albers(), 'NAD_1927_To_WGS_1984_85 + NAD_1927_To_NAD_1983_Alaska')    
        
        raster = '%s_%s_%s_%s_Raster.img' %(glacier, year, day, ident)
        arcpy.PointToRaster_conversion (projected, 'Z', raster, 'MEAN')
        
        elevation = '%s_%s_%s_%s_Formated.shp' %(glacier, year, day, ident)
        arcpy.RasterToPoint_conversion(raster, elevation, 'VALUE')
            
        fields = (('NAME', 'STRING'), ('GLIMSID', 'STRING'), ('YEAR', 'INTEGER'), ('DAY', 'INTEGER'), ('X', 'LONG'), ('Y', 'LONG'), ('Z', 'DOUBLE'))
        for field in fields: arcpy.AddField_management(elevation, field[0], field[1])
        arcpy.DeleteField_management(elevation, 'POINTID')
    
        # Process: Calculate Fields
        desc = arcpy.Describe(elevation).shapeFieldName
        rows = arcpy.UpdateCursor (elevation)
        for row in rows:
            row.setValue('NAME', glacier)
            row.setValue('YEAR', year)
            row.setValue('DAY', day)
            
            featureCenter = row.getValue(desc)
            row.setValue('X', featureCenter.centroid.X)
            row.setValue('Y', featureCenter.centroid.Y)
            row.setValue('Z', row.getValue('GRID_CODE'))
            rows.updateRow(row)
        del row, rows
        
        arcpy.DeleteField_management(elevation, 'GRID_CODE')
        
        output = output_folder + '\\%s_%s_%s_%s.shp' %(glacier, year, day, ident)
        arcpy.SpatialJoin_analysis(elevation, glaciers, output)
        arcpy.CalculateField_management(output, 'GLIMSID', '!GLIMSID_1!', 'PYTHON')
         
        drop_list = ['Join_Count', 'TARGET_FID', 'RGIID', 'GLIMSID_1', 'RGIFLAG', 'BGNDATE', 'ENDDATE', 'CENLON', 'CENLAT', 'O1REGION', 'O2REGION', 'AREA', 'GLACTYPE', 'NAME_1', 'PARK', 'MIN', 'AVG', 'MAX']
        for item in drop_list: arcpy.DeleteField_management(output, item)
            
        envi.delete_items([projected, elevation, profile, raster])
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


def import_lidar (input_folder):
    import database.database_connection   

    # Setup workspace
    envi = environment.setup_arcgis (False, False, False)
    arcpy = envi._arcpy
    
    # Create Database Connection
    DBase = database.database_connection.Database_Connection('munich.gi.alaska.edu', 'spatial_database', 'jrich', 'abc')
    
    counter = {'file': 0, 'record': 0, 'set': 1}
    for shapefile in glob.glob (os.path.join (input_folder, '*.shp')):
        print counter['file'], '-', os.path.basename(shapefile)[0:-4], '(x50000):', 
        
        counter['file'] += 1
        counter['record'] = 0
        counter['set'] = 0
        
        sql = ''
        rows = arcpy.SearchCursor(shapefile)
        for row in rows:        
            data = {'name': row.name, 'glimsid': row.glimsid, 'year': row.year, 'day': row.day,  'x': row.x, 'y': row.y, 'z': row.z}
    
            if counter['record'] == 50000:
                print counter['set'],
    
                DBase._cursor.execute(sql)
                DBase._connection.commit()
                sql = '' #reset SQL string
                
                # Reset and increase counters
                counter['record'] = 0 #reset record counter
                counter['set'] += 1 #Increase the record counter set
            counter['record'] += 1 
            
            sql += """INSERT INTO lidar (name, glimsid, year, day, x, y, z, geom) 
                VALUES ('%s', '%s', %s, %s, %s, %s, %s, ST_GeomFromText('POINT(%s %s %s 0)', 3338));
                """ %(data['name'], data['glimsid'], data['year'], data['day'], data['x'], data['y'], data['z'], data['x'], data['y'], data['z'])
        del row, rows
    
        print 'Final:', (counter['set'] * 50000) + counter['record']
        DBase._cursor.execute(sql)
        DBase._connection.commit()
    DBase.close()
    
    
    

def driver ():
#     input_folder = r'A:\Desktop\Profiler_data'
#     output_folder = r'A:\Desktop\profile_shp'
#     glaciers = r'B:\Data_Glaciers\Alaska_Modern.shp'
#     snap = r'B:\Data_Glaciers\SnapRaster.img'
#     cell_size = 10
#   
#     profile_shapefile (input_folder, output_folder, glaciers, snap, cell_size)
    input_folder = r'A:\Desktop\profile_shp'
    import_lidar (input_folder)
    
if __name__ == '__main__':
    driver ()        
