"""-----------------------------------------------------------------------------
 Name: Image Processor: Image Handler
 Purpose: Script is designed to handle raster datasets so they can be used as
 an array within scripts. This is done by converting an input raster to a 
 numpy array and holding the geo-spatial information for export at a later time.

 Author:      Justin Rich (justin.rich@gi.alaska.edu)

 Created:     Feb. 23, 2011
 Copyright:   (c) glaciologist 2011
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
-----------------------------------------------------------------------------"""
import arcpy                                                 #@UnresolvedImport
import numpy 

class Image (object):
    """Class that deals with layer I/O by holding and storing raster information.
    This class works by becoming an 'Image', storing data in a numpy array in order 
    to facilitate raster manipulation. The 'Image' can be manipulated by changing
    grid cell values or by checking in and out sections of the raster for use in 
    other modules."""
    
    def __init__ (self, filename):
        """Imports multiple rasters and holds a reference to them in order to 
        serve as a 3 dimensional array. Takes in a file name (this includes the 
        directory path)"""      
        self._filename = filename
        
        
    def get_value (self, row, col, band):
        """Returns the value of a pixel at the specified row and column.The
        #functions purpose is to handle exceptions where they exist such as
        'out of bounds' / 'out of range' that occurs when the moving window
        is at an edge."""
        value = 0
        try: value = self._array[row, col, band] # Try and get the value from the image.
        finally: return value # If value can't be obtained return 0
        
        
    def set_value (self, row, col, band, value):
        """Sets the value of a pixel at the specified row and column."""
        # Try and set value in the image
        try: self._layer [row, col, band] = value
        except: return False # If value is not set, return false
        else: True # If value is set, return true
    
    
    def get_location (self):
        """Return the lower left corner coordinates. This is primarily used for saving
        the image or layer to a file."""
        location = arcpy.Point()
        location.X = str(arcpy.GetRasterProperties_management(self._filename, "LEFT"))
        location.Y = str(arcpy.GetRasterProperties_management(self._filename, "BOTTOM"))
        return location
    
    
    def get_spatailreference (self):
        """Return the spatial reference for the image or layer imported."""
        return arcpy.Describe(self._filename).spatialReference


    def get_rows (self):
        """Returns the number of rows in the image."""
        return int(str(arcpy.GetRasterProperties_management(self._filename, 'ROWCOUNT')))


    def get_columns (self):
        """Returns the number of columns in the image"""
        return int(str(arcpy.GetRasterProperties_management(self._filename, 'COLUMNCOUNT')))


    def get_x_cell_size (self):
        """Returns the size of image pixels in the X direction"""
        return arcpy.GetRasterProperties_management(self._filename, 'CELLSIZEX')


    def get_y_cell_size (self):
        """Returns the size of image pixels in the y direction"""
        return arcpy.GetRasterProperties_management(self._filename, 'CELLSIZEY')
    
    
    def get_null_raster (self):
        """Return wether or not am image or layer contains all nodata"""
        return arcpy.GetRasterProperties_management(self._filename, 'ALLNODATA')



class Single_Image (Image):
    """Class that deals with layer I/O by holding and storing raster information.
    This class works by becoming an 'layer', storing data in a numpy array in order 
    to facilitate raster manipulation. The 'layer' can be manipulated by changing
    grid cell values or by checking in and out sections of the raster for use in 
    other modules."""

    def __init__(self, filename):
        """Imports a single raster file and returns an array. Takes in a file name
        (this includes the directory path)"""                             
        self._filename = filename
        self._layer = arcpy.RasterToNumPyArray(filename)


    def get_value (self, row, column):
        """Returns the value of a pixel at the specified row and column.The
            #functions purpose is to handle exceptions where they exist such as
            'out of bounds' / 'out of range' that occurs when the moving window
            is at an edge."""
        value = 0
        try: value = self._layer [row, column] # Try and get the value from the image.
        finally: return value # If value can't be obtained return 0
     
     
    def set_value (self, row, column, value):
        """Sets the value of a pixel at the specified row and column."""
        # Try and set value in the image
        try: self._layer [row, column] = value
        except: return False # If value is not set, return false
        else: True # If value is set, return true
               

    def save (self, output, nodata_value = 0):
        """Save image to a raster dataset. Format should be specified in the output
        file name (i.e. *.img, *.tif, *.jpg... etc.)"""
        raster = arcpy.NumPyArrayToRaster(self._layer, self.get_location(), self._filename, self._filename, nodata_value)
        arcpy.DefineProjection_management(raster, self.get_spatailreference())
        raster.save (output)

         
    def get_tile (self, x, width):
        """Returns a numpy array created from the image based on the column X and
        the size of width."""         
        xd = x # Tile Width
        tile = numpy.zeros((self.get_rows() ,width)) # Empty grid to fill
        for c in range(0, width): # Iterate through array and get values
            for r in range(0, self.get_rows()):
                tile[r , c] = self.get_value (r, xd)
            xd +=1
        return tile  # Pass grid


    def return_tile (self, tile, x, width):
        """Takes in a numpy array and places it in the image based on the
        column X and the size in based on width."""
        xd = x # Tile Width
        for c in range(0, width): # Iterate through array and set values
            for r in range(0, self.get_rows()):
                self.set_value(r, xd, (tile [r, c]))
            xd +=1


class Folder (Image):
    """Class that deals with layer I/O by holding and storing raster information.
    This class works by becoming an 'layer', storing data in a numpy array in order 
    to facilitate raster manipulation. The 'layer' can be manipulated by changing
    grid cell values or by checking in and out sections of the raster for use in 
    other modules. This class differs from 'Image' in that it takes in single band
    files located in a folder to assemble the n-d array."""
    
    def __init__(self, folder, extention = '*img'):
        """Imports multiple rasters and holds a reference to them in order to 
        serve as a 3 dimensional array. Takes in a folder name (this includes the 
        directory path)"""      
        import os
        import glob
        
        arrays = list()
        files = [files for files in glob.glob (os.path.join (folder, extention))]
        for file_name in files: 
            arrays.append(arcpy.RasterToNumPyArray(file_name))
        
        try: 
            self._files = files
            self._filename = files[0]
            self._array = numpy.dstack(arrays)
        except: print 'ERROR: Folder Maybe Empty.'
        
        del arrays, files
        
        
        
    def save (self, output, nodata_value = 0):
        """Save image array to a raster dataset. Format should be specified in the 
        output file name (i.e. *.img, *.tif, *.jpg... etc.)"""
        pass
        
        
#_______________________________________________________________________________
#***  DRIVER *******************************************************************
def driver ():
    test = Single_Image('A:\Desktop\LASTestRuns\Miles2009-2011\RandomRaster.img')
    print test.get_value(1, 2)
    print test.get_location()
    print test.get_rows()
    print test.get_columns()
    
if __name__ == '__main__':
    driver()