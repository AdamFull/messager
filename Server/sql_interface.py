import sqlite3

class SqlInterface:
    def __init__(self, dbname=None):
        self.connection = None
        self.cursor = None
        if dbname:
            self.connect(dbname)
    
    def connect(self, dbname):
        try:
            self.connection = sqlite3.connect(dbname)
            self.cursor = self.connection.cursor()
            return True
        except sqlite3.Error as e:
            print('Error to open database.')
            self.close()
            return False
    
    def create_table(self, table_name, table_columns):
        self.cursor.execute("""CREATE TABLE %s (%s);""" % (table_name, table_columns))
    
    def delete_table(self, table_name):
        self.cursor.execute("""DROP TABLE %s""" % table_name)
    
    def get(self, table_name, columns, limit=None):
        self.cursor.execute("""SELECT %s from %s;""" % (columns, table_name))
        rows = self.cursor.fetchall()
        return rows[len(rows)-limit if limit else 0:]
    
    def find_by_id(self, table_name, id):
        self.cursor.execute("")
    
    def insert(self, table_name, columns, data):
        self.cursor.execute("""INSERT INTO %s (%s) VALUES (%s);""" % (table_name, columns, data))
    
    def query(self, sql):
        self.cursor.execute(sql)
    
    def close(self):
        if self.connection:
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, ex_type, ex_value, traceback):
        self.close()