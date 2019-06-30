#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
import encryption
def crypro_test():
    msg = "hello world"
    aes = encryption.AESCrypt()
    crypted = aes.encrypt(msg)
    decrypted = aes.decrypt(aes.getKey(), crypted)
    #print(crypted)
    #print(decrypted)
    assert (decrypted == msg), 'Decryption fail!'
"""

from Client import client
from Client import encryption
from Server import server
from threading import Thread
import time, random, string, sys
from Server.sql_interface import SqlInterface


TEST_MESSAGE = "Hello, World"
message_queue = list()

class SqlTests:
    def __init__(self):
        self.database_path = 'Server/Data/server_database.db'
        self.sql_interface = SqlInterface(self.database_path)
    
    @staticmethod
    def __generate_random_names(self, number_of_names):
        names = []
        for i in range(number_of_names):
            temp = ""
            for j in range(number_of_names * 5):
                temp += random.choice(string.ascii_letters)
            names.append(temp)
        return names

    @staticmethod
    def __generate_table(self):
        print("Generating table test with values.")
        self.sql_interface.create_table("test", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT")
        names = self.__generate_random_names(self, 5)
        for name in names:
            self.sql_interface.insert("test", "name", [name])
        return names
        

    def print_tables_in_database(self):
        print(self.sql_interface.table_list(), "\n")
    
    def create_table_test(self):
        print("Creating table test.")
        self.__generate_table(self)
        self.print_tables_in_database()
    
    def delete_table_test(self):
        print("Deleting table test.")
        self.sql_interface.delete_table("test")
        self.print_tables_in_database()
    
    def get_values_by_column_test(self):
        print("Get all column values.")
        self.__generate_table(self)
        print(self.sql_interface.get("test", "name"))
        self.delete_table_test()
    
    def find_rows_by_value_test(self):
        print("Find rows by value.")
        names = self.__generate_table(self)
        print(self.sql_interface.find("test", "name", names[1]))
        self.delete_table_test()
    
    def fetch_table_data_test(self):
        print("Fetch all table data.")
        self.__generate_table(self)
        print(self.sql_interface.fetch_all("test"))
        self.delete_table_test()
    
    def update_row_test(self):
        print("Update row values.")
        self.__generate_table(self)
        print(self.sql_interface.find("test", "id", 1))
        self.sql_interface.update("test", "name", ['mikhail', 1])
        print(self.sql_interface.find("test", "id", 1))
        self.delete_table_test()

    def delete_row_test(self):
        print("Delete row from table.")
        self.__generate_table(self)
        print(self.sql_interface.fetch_all("test"))
        self.sql_interface.delete("test", 1)
        print(self.sql_interface.fetch_all("test"))
        self.delete_table_test()

    


def store_messages(raw_data):
    print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))
    message_queue.append(raw_data)

def RSA_test():
    rsa_class = encryption.RSACrypt()
    print("Public key: ", rsa_class.get_pub())
    print("Private key: ", rsa_class.get_priv())


def simple_exchange_test():
    srv = server.Server()
    server_thread = Thread(target=srv.run)
    server_thread.start()

    cli1 = client.Client(receive_callback=store_messages)
    cli2 = client.Client(receive_callback=store_messages)

    message_queue.clear()

    time.sleep(1.0)
    cli1.send(TEST_MESSAGE)
    #TODO compare recieved messages

    srv.stop()
    server_thread.join()


if __name__ == "__main__":
    sql_tests = SqlTests()
    sql_tests.print_tables_in_database
    sql_tests.create_table_test()
    sql_tests.delete_table_test()
    sql_tests.get_values_by_column_test()
    sql_tests.find_rows_by_value_test()
    sql_tests.fetch_table_data_test()
    sql_tests.update_row_test()
    sql_tests.delete_row_test()
    input("Press enter to continue...")

    try:
        simple_exchange_test()

    except AssertionError as e:
        print(e)
