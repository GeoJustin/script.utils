"""****************************************************************************
 Name:         shapefile.format_featureclass
 Purpose:     
 
Created:         Oct 18, 2013
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
import sys

class FormatFeatureClass (object):
    """classdocs: Creates an instance of Format Feature Class, a class designed 
    to reformat a shapefile into another format. Old fields are either deleted
    or copied into a new column based on the mapping dictionary"""
    
    HEADERS = {
    'RGI': [['RGIID', 'TEXT', '', '', '14'], ['GLIMSID', 'TEXT', '', '', '14'], ['RGIFLAG', 'TEXT', '', '', '14'], 
        ['BGNDATE', 'TEXT', '', '', '8'],  ['ENDDATE', 'TEXT', '', '', '8'], ['CENLON', 'FLOAT', '', '', ''],   
        ['CENLAT', 'FLOAT', '', '', ''], ['O1REGION', 'SHORT', '', '', ''], ['O2REGION', 'SHORT', '', '', ''],
        ['AREA', 'DOUBLE', '10', '3', ''], ['GLACTYPE', 'TEXT', '', '', '4'], ['NAME', 'TEXT', '', '', '50']],
               
    'RGI_PARKS': [['RGIID', 'TEXT', '', '', '14'], ['GLIMSID', 'TEXT', '', '', '14'], ['RGIFLAG', 'TEXT', '', '', '14'], 
        ['BGNDATE', 'TEXT', '', '', '8'],  ['ENDDATE', 'TEXT', '', '', '8'], ['CENLON', 'FLOAT', '', '', ''],   
        ['CENLAT', 'FLOAT', '', '', ''], ['O1REGION', 'SHORT', '', '', ''], ['O2REGION', 'SHORT', '', '', ''],
        ['AREA', 'DOUBLE', '10', '3', ''], ['GLACTYPE', 'TEXT', '', '', '4'], ['NAME', 'TEXT', '', '', '50'],                
        ['PARK', 'TEXT', '', '', '4'],['MIN', 'DOUBLE', '10', '3', ''], ['AVG', 'DOUBLE', '10', '3', ''],
        ['MAX', 'DOUBLE', '10', '3', '']]   
    }

    def __init__(self):
        """Constructor: Takes in a format type, input, output and mapping
        to generate a newly formated shapefile. REQUIRES the arcpy module
        to run"""
        try: 
            import arcpy
            self._arcpy = arcpy
        except: return False
            
                
    def featurechecks (self, input_file):
        arcpy = self._arcpy
        desc = arcpy.Describe(input_file)
        
        if desc.shapeType <> 'Polygon': 
            print 'ERROR: Input feature is not a polygon'
        
                
    def format (self, input_file, output_file, format_type, mappings = {}):
        """Takes an input shapefile and outputs a new shapefile
        formated based on the rgi format"""
        arcpy = self._arcpy
        
        print "Input File: " + os.path.basename(input_file)
        print "Output File: " + os.path.basename(output_file)
        print 'Output Folder: ' + os.path.dirname(os.path.abspath(output_file))
        print ''
        
        # Create a copy of the input file in the output folder. This will be the
        # actual result file after fields are updated. This is done so no changes
        # are imposed on the original file.
        try: new_file = arcpy.CopyFeatures_management(input_file, output_file)
        except: sys.exit('Output Glacier file already exists or the output folder is not available.')

        # List of original field names in the file that will be deleted or re-mapped
        original_fields = [] 
        fields_list = arcpy.ListFields(new_file)
        for field in fields_list: # Loop through the field names
            if not field.required: # If they are not required append them to the list of field names.
                original_fields.append(field.name)
        
        # Print run time parameters
        print 'Original Field Names:'
        print '    ' + ', '.join(original_fields)   
        print 'Field Mapping:'      
        print '    ' + str(mappings)
        print 'Fields Added:'    
                
        # Create a temporary field for each of the fields to be re-mapped
        counter = 1 # temporary field number
        temp_fields = [] # temporary fields to delete later
        for key in mappings:
            temp_field = 'TEMP_' + str(counter) # temporary Field name
            arcpy.AddField_management (new_file, temp_field, 'TEXT', '', '', 50)
            
            arcpy.CalculateField_management (new_file, temp_field, '!' + mappings[key] + '!', 'PYTHON')

            mappings [key] = (temp_field)
            temp_fields.append(temp_field) # Add temporary field to list
            counter += 1 # Increment the counter by 1

        # If the mapping has nothing to map, create a temporary null field to prevent
        # errors resulting from features needing at least one field
        if not mappings:  
            arcpy.AddField_management (new_file, '__HOLDER__', 'TEXT')  
            temp_fields.append('__HOLDER__')
        
        # Drop all original fields
        arcpy.DeleteField_management (new_file, original_fields)

        # Create New RGI Headers
        for header in self.HEADERS[format_type]:
            print '    ' + ', '.join(header)
            arcpy.AddField_management (new_file, header[0], header[1], header[2], header[3], header[4])
        
        # Map temporary fields to new fields and delete the temporary fields
        for key in mappings:
            arcpy.CalculateField_management (new_file, key, '!' + mappings[key] + '!', 'PYTHON')
            
        arcpy.DeleteField_management (new_file, temp_fields) # Drop temporary fields
        
        
        
        #_______________________________________________________________________________
#***  DRIVER *******************************************************************
# HARD CODE INPUTS HERE !
def driver():
    pass
if __name__ == '__main__':
    driver()
