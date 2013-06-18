"""****************************************************************************
 Name:         Database Connection
 Purpose:     This class is designed to working with psycopg2 in order to open
     maintain and use a connection to a postgresSQL database. 
 
Created:         Jun 10, 2013
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
import external_packages.psycopg2 as psycopg2 

class Database_Connection (object):
    
    def __init__ (self, host , database, user, password):
        """Constructor: sets up an initial connection to a database given the 
        host server and database name."""
        self._host = host
        self._database = database
        self._user = user
        self._password = password

        connection, cursor = self.connect()
        self._connection = connection
        self._cursor = cursor

    
    def connect (self):
        """Connect creates new database session and returns connection and cursor 
        object object. This method is called on instantiation of the class but is left
        as a separate function so that it could be manually called again later if needed."""
        connection  = psycopg2.connect(" host='%s' dbname='%s' user='%s' password='%s'" %(self._host, self._database, self._user, self._password))
        cursor = connection.cursor() # Cursor object
        return connection, cursor
    
    
    def execute (self, sql):
        """Execute a SQL queary on the current dataset """
        self._cursor.execute("""%s""" %(sql))
        
        
    def create_table (self, table, columns = '', pkey = 'pkey'):
        """Create a new, basic, table in a database. 'Columns' refers to the columns in 
        the table, other then the primary key, and should be specified as a string of 
        SQL. For example: "name type NOT NULL, name type,..."""
        self._cursor.execute("CREATE TABLE %s (%s serial NOT NULL, %s, CONSTRAINT %s PRIMARY KEY (%s));" %(table, pkey, columns, table + pkey, pkey))
        self._connection.commit()
        
        
    def copy_table (self, table):
        """Copies a tables header information to a new table"""
        self._cursor.execute("CREATE TABLE processing_table (LIKE %s INCLUDING ALL);" %(table))
        self._connection.commit()
        
    
    def insert_record (self, table, value_map):
        """Insert records into the given table. This function takes in a dictionary
        to map values to fields. String fields need to include single quotes (' ') 
        around the value. This should be done in the value_map for example:
        name: "'" + value + "'" """
        fields = [str(field) for field in value_map.keys()]
        values = [str(value) for value in value_map.values()]
         
        self._cursor.execute("INSERT INTO %s (%s) VALUES (%s);" %(table, ','.join(fields), ','.join(values)))
        self._connection.commit()
        
        
    def update_record (self, table, value_map, where):
        """Update records where a condition is met. The where clause should be in the 
        form of "Field = Value AND Field = Value"...etc.  This function will update all
        fields that satisfy the where clause so care should be taken if this is not the 
        result wanted"""
        set_values = ''
        for key, value in value_map.iteritems(): 
            set_values += "%s = %s," %(key, value)
        self._cursor.execute("UPDATE %s SET %s WHERE %s;" %(table, set_values [0:-1], where))
        self._connection.commit()
        
        
    def upsert_record (self, table, join_tuple, value_map):
        """Upsert is a combination of Update and Insert. If a record already exists,
        defined by weather or not the join_tuple matches, an update
        of the record is carried out, if the record does not exist an insert is executed
        and if there are many records already, nothing is added to the table and the
        join tuple is passed back. The join tuple should consist of 1 or more fields in the
        table. NOTE ('field') is not a tuple but a string in parentheses ('field',) is a tuple"""
        # Generate a where clause and select all rows with those values
        where = [field + ' = ' + str(value_map[field]) for field in join_tuple]
        exists = self.get_selection(table, ' AND '.join(where))
         
        if   len(exists) == 0: # If no records are selected: INSERT row
            self.insert_record(table, value_map)
            return None
        elif len(exists) == 1: # If one record is selected: UPDATE row
            self.update_record(table, value_map, ' AND '.join(where))
            return None
        else: return exists # If multiple records are selected return the rows
             
    
    def remove_duplicates (self, table):
        """NOT WRITEN"""
        return True
    
    
    def close (self):
        """Close the connection to the database """
        self._connection.close()
    
    
    def get_tables (self):
        """Get all tables in the database and return them as a list of tuples"""
        self._cursor.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'""")
        return self._cursor.fetchall() # Get data resulting from the SQL statement
    
    
    def get_records (self, table):
        """Get all records from a given table and returns them as a list of tuples.
        This method is useful for small tables by is likely not viable for large ones.
        In this case a server side cursor should be setup (http://wiki.postgresql.org/wiki/Using_psycopg2_with_PostgreSQL)"""
        self._cursor.execute("""SELECT * FROM %s""" %(table))
        return self._cursor.fetchall() # Get data resulting from the SQL statement
    
    
    def get_selection (self, table, where):
        """ Get all records from a given table that satisfy a given where clause
        and returns them as a list of tuples. The where clause should be in the 
        form of "Field = Value AND Field = Value"...etc."""
        self._cursor.execute("SELECT * FROM %s WHERE %s;" %(table, where))
        return self._cursor.fetchall()
        
    
    def get_version (self):
        """Get Database version information """
        self._cursor.execute('SELECT version()') # Executes SQL statement 
        return self._cursor.fetchall() # Get data resulting from the SQL statement
    
    
def driver ():
    pass
if __name__ == '__main__':
    driver ()        
