import sqlite3
from os import path, makedirs
from configparser import ConfigParser
from os.path import isfile, exists
from hashlib import sha256
from random import choice
from string import ascii_letters, punctuation, digits
from protocol import Protocol, AESCrypt, RSACrypt

sha = lambda X: sha256(X.encrypt()).hexdigest()

class SqlInterface:
    def __init__(self, dbname=None):
        self.connection = None
        self.cursor = None
        if dbname:
            self.create_database(dbname)
    
    def connect(self, dbname):
        try:
            self.connection = sqlite3.connect(dbname, check_same_thread=False)
            self.cursor = self.connection.cursor()
            return True
        except sqlite3.Error as e:
            print('Error to open database.')
            self.close()
            return False
    
    def create_database(self, dbname):
        if not self.connect(dbname):
            self.connect(dbname)
            self.close()
            return True
        else:
            self.connect(dbname)
            return False
    
    def create_table(self, table_name, table_columns):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS %s (%s);' % (table_name, table_columns))
        self.connection.commit()
    
    def delete_table(self, table_name):
        self.cursor.execute('DROP TABLE %s' % table_name)
        self.connection.commit()
    
    def get(self, table_name, columns, limit=None):
        self.cursor.execute('SELECT %s from %s;' % (columns, table_name))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def table_list(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]

    def table_exists(self, table_name):
        pass

    def fetch_all(self, table_name):
        self.cursor.execute("SELECT * FROM %s;" % table_name)
        data = self.cursor.fetchall()
        return [list(elt) for elt in data]

    def find(self, table_name, parameter, value):
        query = 'SELECT * FROM %s WHERE "%s" = ?;' % (table_name, parameter)
        self.cursor.execute(query, [value])
        data = self.cursor.fetchall()
        return [list(elt) for elt in data]
    
    def insert(self, table_name, columns, data):
        query_val = "?,"*len(data)
        query = 'INSERT INTO %s (%s) VALUES (%s);' % (table_name, columns, query_val[:len(query_val)-1])
        self.cursor.execute(query, data)
        self.connection.commit()
    
    def update(self, table_name, columns, values):
        cols = columns.replace(" ", "").split(",")
        query = 'UPDATE %s SET %s WHERE "id" = ?;' % (table_name, ' = ?, '.join(cols) + ' = ?')
        self.cursor.execute(query, values)
        self.connection.commit()

    def delete(self, table_name, id):
        query = 'DELETE FROM %s WHERE id = ?;' % table_name
        self.cursor.execute(query, str(id))
        self.connection.commit()
    
    def query(self, sql):
        self.cursor.execute(sql)
        self.connection.commit()
    
    def close(self):
        if self.connection:
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, ex_type, ex_value, traceback):
        self.close()

class ServerDatabase(SqlInterface):
    def __init__(self):
        self.data_path = 'Data/'
        self.database_path = self.data_path + "server_database.db"

        if not exists(self.data_path):
            makedirs(self.data_path)

        self.create_database(self.database_path)
        self.create_table("users", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, public_key TEXT, verification INTEGER, invite_word TEXT")
        self.create_table("invite_keys", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, invite_hash TEXT")
        self.create_table("accessories", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, room TEXT, role TEXT")
        self.create_table("friends", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, friend TEXT")

    def add_to_accessories(self, user, room, role):
        self.insert("accessories", "username, room, role", (user, room, role))
    
    def remove_from_accessories(self, user, room):
        self.query('DELETE FROM %s WHERE username=%s AND room=%s' % ("accessories", user, room))
    
    def create_room(self, room_name, user):
        self.create_table(sha(room_name), "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, setting TEXT, value TEXT")
        self.insert(sha(room_name), "description, send_messages, send_media, send_stickers, embded_links, send_polls, add_members, pin_messages, change_group_info",
                                    ("It is group", "T", "T", "T", "T", "T", "T", "T", "T"))
        self.add_to_accessories(user, room_name, "owner")
    
    def load_room(self, room_name):
        self.query('SELECT * FROM %s;' % (sha(room_name)))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def remove_room(self, room_name):
        self.delete_table(sha(room_name))
        self.query('DELETE FROM %s WHERE room=%s;' % ("accessories", room_name))
    
    def get_users_in_room(self, room_name):
        self.query('SELECT user FROM %s WHERE room=%s;' % ("accessories", room_name))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def get_rooms(self):
        self.query('SELECT room FROM %s;' % "accessories")
    
    def get_user_rooms(self, user):
        self.query('SELECT room FROM %s WHERE user=%s;' % ("accessories", user))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def get_finded_users(self, username):
        self.query('SELECT username FROM %s WHERE username LIKE %s' % ("users", username))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def get_finded_rooms(self, room_name):
        self.query('SELECT room FROM %s WHERE room LIKE %s;' % ("accessories", room_name))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def get_friends(self, user):
        self.query('SELECT friend FROM %s WHERE username= %s;' % ("friends", user))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def add_friend(self, user, friend):
        self.insert("friends", "username, friend", (user, friend))


    def __generate_key(self, length):
        return ''.join(choice(ascii_letters + digits + punctuation) for i in range(length))

    def is_user_already_exist(self, username):
        return True if len(self.find("users", "username", username)) > 0 else False
    
    def is_user_verificated(self, username):
        return True if self.find("users", "username", username)[0][3] == 1 else False
    
    def is_keys_match(self, username, public_key):
        return True if public_key in self.find("users", "username", username)[0] else False
        
    def is_invite_hash_match(self, username, invite_hash):
        return True if self.find("invite_keys", "username", username)[0][2] == invite_hash else False
    
    def get_user_id(self, table_name, username):
        return self.find(table_name, "username", username)[0][0]
    
    def add_user_without_verification(self, username, public_key):
        self.insert("users", "username, public_key, verification", (username, public_key, True))
    
    def add_user_with_verification(self, username, public_key):
        word = self.__generate_key(32)
        self.insert("users", "username, public_key, verification, invite_word", (username, public_key, False, word))
        invite_hash = sha(word)
        self.insert("invite_keys", "username, invite_hash", (username, invite_hash))
    
    def verificate_user(self, username, invite_hash):
        if self.is_invite_hash_match(username, invite_hash):
            self.update("users", "verification", [True, self.get_user_id("users", username)])
            self.update("invite_keys", "invite_hash", ['VERIFICATED', self.get_user_id("invite_keys", username)])
            return True
        else:
            return False
    

class ServerSettings:
    def __init__(self):
        self.config = ConfigParser()
        self.config_path = 'config.ini'
        self.server_ip = '0.0.0.0'
        self.server_port = 9191
        self.maximum_users = 100
        self.enable_password = False
        self.enable_whitelist = False
        self.whitelist = []
        self.server_rooms = ['guest' ,'proggers', 'russian', 'pole']
        self.protocol = Protocol()

        if isfile(self.config_path):
            if not isfile("private.pem"):
                self.private_key = RSACrypt().export_private()
                self.save_key()
            self.load()
        else:
            self.save()

    def encrypt_key(self, key, user_key):
        return RSACrypt().encrypt(key, user_key)

    def save(self):
        self.config["NET"] = {"server_ip" : self.server_ip, "server_port" : self.server_port}
        self.config["SETTINGS"] = {"max_slots" : self.maximum_users, "enable_password" : self.enable_password, "server_password" : self.server_password, "enable_whitelist" : self.enable_whitelist,
                                   "white_list" : self.whitelist, "rooms" : self.server_rooms}

        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)
        self.save_key()
    
    def getlist(self, string):
        return (''.join(i for i in string if not i in ['[', ']', '\'', ' '])).split(',')
    
    def load_key(self):
        with open('private.pem', "rb") as pem_file:
            return AESCrypt(sha(self.server_ip)).decrypt(pem_file.read())

    def save_key(self):
        with open('private.pem', "wb") as pem_file:
            key = AESCrypt(sha(self.server_ip)).encrypt(self.private_key)
            pem_file.write(key)

    def load(self):
        self.config.read(self.config_path)
        self.server_ip = self.config["NET"].get("server_ip")
        self.server_port = self.config["NET"].getint("server_port")
        self.maximum_users = self.config["SETTINGS"].getint("max_slots")
        self.enable_password = self.config["SETTINGS"].getboolean('enable_password')
        self.enable_whitelist = self.config["SETTINGS"].getboolean('enable_whitelist')
        self.whitelist = self.getlist(self.config["SETTINGS"].get('white_list'))
        self.server_rooms = self.getlist(self.config["SETTINGS"].get('rooms'))
        private_key = self.load_key()
        self.protocol.load_rsa(private_key)