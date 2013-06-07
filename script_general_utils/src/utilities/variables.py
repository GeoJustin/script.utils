"""****************************************************************************
 Name: postProcessing.modules.variables
 Purpose: Stores and calls variables to be used by the application. This module
         works with a configuration file and stores the information perminatly
         so that changes are remembered between runs.
 
Created: Jul 25, 2012
Author:  Justin Rich (justin.rich@gi.alaska.edu)
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
import glob

class Variables (object):
    """Stores and calls variables to be used by the application. This module
       works with a configuration file and stores the information perminatly
       so that changes are remembered between runs."""
  
    def __init__ (self):
        """ init starts the variables module and locates the associated .var
        file to be used. The .var file must be located at the same path as the
        module or an error will be generated."""
        
        self.__variables = '' #Store the path of the variables file
        
        path = os.path.dirname(os.path.abspath(__file__)) # Get modules path.
        # Search files in path with the extension .var and add the path to it.
        for f in glob.glob (os.path.join (path, '*.var')): 
            self.__variables = path + '\\' + os.path.basename(f) 


    def read_variable (self, var_name):
        """Read a variable from the .var file and return its value."""
        variables = open (self.__variables, 'r')
        for line in variables:
            if line[0] <> '#': # Don't bother reading note lines
                # Remove spaces and page breaks in order to create a list of
                # just variable name and value.
                var_line = (line.replace(' ', '').replace('\n', '')).split ('=')
                if var_line [0] == var_name: 
                    if var_line [1] == 'STRING': # Return the value as a string
                        return var_line [2] 
                        break
                    if var_line [1] == 'INTEGER': # Return the value as an int
                        return int(var_line [2]) 
                        break 
                    if var_line [1] == 'FLOAT': # Return the value as a float
                        return float(var_line[2])
                        break
                    if var_line [1] == 'BOOLEAN': # Return the value as boolean
                        return var_line[2] in ('True', '1')
                        break
                    if var_line [1] == 'LIST': # Return the value as a list
                        return var_line [2].replace(' ', '').split (',')
                        break
                    if var_line [1] == 'LISTS': # Return the value as a list
                        list_strings = var_line [2].replace(' ', '').split (',')
                        for index, item in enumerate (list_strings):
                            list_strings [index] = item.replace('(', '').replace(')', '').split(';')
                        return list_strings
                        break
        variables.close() # Close the file and discard reference.
        return 'VARIABLE NOT FOUND' # Return value if no variable is found.

        
    def set_variable (self, var_name, var_type, var_value):
        """Write a new variable to the .var file, replacing the original."""
        variables = open (self.__variables, 'r')
        var_list = [] #List to hold contents of .var file.
        result = "VALUE NOT SET" # Return value
        for line in variables:
            var_list.append(line) # Add items (lines) to var_list.
        variables.close() # Close the file and discard reference.
          
        new_variables = open (self.__variables, 'w')  
        for item in var_list:
            if item[0] <> '#': # Don't bother reading note lines
                # Remove spaces and page breaks in order to create a list of
                # just variable name and value.
                var_line = (item.replace(' ', '').replace('\n', '')).split ('=')
                if var_line [0] == var_name: # If value is found replace with new
                    item = str(var_name) + ' = ' + var_type + ' = ' + str(var_value) + '\n'
                    result = "VALUE SET"
            new_variables.write(item) # Write line to file.
        new_variables.close() # Close the file and discard reference.
        return result
    
    
    def reset_defaults (self):
        """Iterate through the .var document and reset the default values of
        all variables to their original state using the set_variables method.""" 
        variables = open (self.__variables, 'r')
        var_list = [] #List to hold contents of .var file.
        for line in variables:
            var_list.append(line) # Add items (lines) to var_list.
        variables.close() # Close the file and discard reference.
        
        
        for item in var_list:
            if item[0] <> '#': # Don't bother reading note lines
                # Remove spaces and page breaks in order to create a list of
                # just variable name and value.
                var_line = (item.replace(' ', '').replace('\n', '')).split ('=')
                # If value is found replace with new value (-1 is not found)
                if var_line [0].find('(Default)') <> -1:
                    #Reset the default value using the set_variable method
                    self.set_variable(var_line[0].replace('(Default)', ''), var_line[1], var_line[2])
        return "RESET COMPLETE"
        
        
#Driver
def main():
    pass
if __name__ == '__main__':
    main()