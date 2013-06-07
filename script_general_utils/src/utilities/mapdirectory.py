"""****************************************************************************
 Name:         mapdirectory
 Purpose:

Created:         May 9, 2013
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

class mapdirectory (object):
    '''Map Directory: As it's name suggests is used to map directories.
    Specifically, it is used to search for files off a certain type or look
    for files that have specific text in their name.'''

    def __init__ (self):
        '''Start the class, store the initial directory path and run the 
        first search.'''
        pass


    def list_contents (self, dir_path, search_filter = [], __results = []):
        '''List Contents is a function designed to recursively move down
        through a directory and return all files. A filter can 
        be applied to this search.'''
        dir_list = os.listdir(dir_path)
        for item in dir_list:
            full_path = dir_path + '\\' + item
            if os.path.isdir(full_path) == False:
                if len(search_filter) == 0: __results.append(full_path)
                else:
                    for item in search_filter:
                        if full_path.find(item) is not -1: __results.append(full_path)
            elif os.path.isdir(full_path) == True:
                try: self.list_contents(full_path, search_filter, __results)
                except: pass
        return __results
    
    
#_______________________________________________________________________________
#***  DRIVER *******************************************************************
def main():
    input_directory = r'A:\Desktop\LAS_Database\Glaciers'
    search_filter = []
    md = mapdirectory()
    results = md.list_contents(input_directory, search_filter)

    print results
if __name__ == '__main__':
    main()
