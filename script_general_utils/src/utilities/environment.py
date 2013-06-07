"""****************************************************************************
 Name:         glacier_utilities.general_utilities.environment
 Purpose:      This class handles general, repetative, operation common when 
 running tasks which use the arcpy module. This includes importing the module
 (with spatial license if applicable) and creating and cleaning up a scratch 
 workspace. 
 
Created:         Nov 16, 2012
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
import os
import sys

class setup_arcgis (object):
    """Sets up a work environment for working with ArcGIS. Class is designed
    to reduce redundant entries across multiple scripts."""

    def __init__(self, output_folder, arcinfo = False, spatial = False):
        """Constructor:  Sets up an Arc GIS work environment"""
        self._output = output_folder    # Set Output Folder to Variable
        self._arcpy = object            # Set Arc Module to a Variable
        self._arcinfo = object          # Set Arc Info License if used
        self._spatial = object          # Set Arc Spatial Analyst if used
        self._workspace = object        # Set workspace to a Variable
        self._log = object              # Setup log file variable
        
        self._import_arcinfo = arcinfo         # Set arc info imported True / False
        self._import_spatial = spatial         # Set spatial license imported True / False
        self.setup_arcgis_workspace()
    
    
    def setup_arcgis_workspace (self):
        """Function: Setup ArcGIS workspace
        Imports the ArcPy module, sets up a workspace, starts a log file
        and then returns them"""
        # Start Log file and write it to the output folder
        try: 
            import output_file.output_file_log
            log = output_file.output_file_log.Log(self._output)
            self._log = log                    # Set log file to variable
        except: sys.exit('Log file could not be written to the output folder.')
        
        try: 
            import arcpy
            self._arcpy = arcpy
        except: 
            log.print_line('Could NOT import arcpy module')
            sys.exit('WARNING - Could NOT import arcpy module')
        
        try: # Set environment
            scratch_space = self._output + '\\scratch'
            os.makedirs(scratch_space) # Create Workspace
            arcpy.env.workspace = scratch_space
            self._workspace = scratch_space  # Set workspace Variable
        except:
            log.print_line('WARNING - Workspace folder already exists.')
            sys.exit('WARNING - Workspace folder already exists.')
        
        if self._import_arcinfo == True: # If arc info is needed
            try:  
                import arcinfo  # Get ArcInfo License if it's available
                self._arcinfo = arcinfo
            except:
                log.print_line('ArcInfo license NOT available')
                sys.exit('ArcInfo license NOT available')

        if self._import_spatial == True: # If arc GIS spatial analysis is needed
            try: # Check out Spatial Analyst extension if available.
                arcpy.CheckOutExtension('Spatial')
                from arcpy import sa
                self._spatial = sa
                log.print_line('Spatial Analyst is available')
            except:
                log.print_line('Spatial Analyst extension not available')
                sys.exit('Spatial Analyst extension not available')
        
    
    
    def delete_items (self, items = []):
        """Function: Delete Items
        Takes a list of items and deletes them one by one using the 
        Delete tool within ARCPY"""
        deleted_all = True
        for item in items:
            try: self._arcpy.Delete_management(item)
            except: deleted_all = False
        return deleted_all
    

    def remove_workspace (self):
        """Function: Remove Workspace
        Removes the workspace held by this function"""
        try: self._arcpy.Delete_management(self._workspace)
        except: return False
        return True


def driver ():
    feature = r'A:\Desktop\LASTestRuns\Novatak2009-2011\Novatak_Glacier.shp'
    scratch = r'A:\Desktop\LASTestRuns\Novatak2009-2011'
    output = r'A:\Desktop\LASTestRuns\Novatak2009-2011\Novatak_SnapRaster.img'
    env = setup_arcgis (scratch)
    env.create_snap_raster(feature, scratch, output, 10, 10)
if __name__ == '__main__':
    driver()