"""****************************************************************************
 Name:         database.database_functions
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

def database_spatialupdate (self, DBase, table, where, feature, xy_dict = {'X': None, 'Y': None}):
    """ This function takes in a database and table connection, along with
    a shapefile of polygon features to determine where table features fall
    spatially among the polygon features. This assumes there is X , Y data
    in the original table. dictionary 'feature' should hold the where selection 
    and dictionary x , y should hold the X and Y positions  """
    import utilities.projection as projection
    import arcpy  # @UnresolvedImport
    
    selection = 'Selection'
    arcpy.MakeFeatureLayer_management (feature, selection)

    points = DBase.get_selection(table , "%s" %(where))
    for point in points:
        X = point[xy_dict['X']]
        Y = point[xy_dict['Y']]
        location = arcpy.PointGeometry(arcpy.Point(X, Y), projection.alaska_albers())
        
        rows = arcpy.SearchCursor(selection)
        for row in rows: 
            name = 'None'
            if location.within(row.Shape):
                name = row.name
                break

        DBase.update_record(table, {'name': "'" + name + "'"}, "x = %s AND y = %s" %(X, Y))
        
            
            
def driver ():
    pass
    
if __name__ == '__main__':
    driver ()     