import sqlite3
from os import makedirs
from configparser import ConfigParser
from os.path import isfile, exists, dirname, abspath
from hashlib import sha256
from random import choice
from string import ascii_letters, punctuation, digits
from protocol import Protocol, AESCrypt, RSACrypt
from threading import Lock

normalize = lambda arr: list(dict.fromkeys([item for sublist in arr for item in sublist]))
sha_hd = lambda x: sha256(x.encode()).hexdigest()
sha_d = lambda x: sha256(x.encode()).digest()
get_cn = lambda x, y: "chat%s" % sha256(x.encode() + y).hexdigest()

lock = Lock()


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
    
    def query(self, sql, args=None):
        lock.acquire(True)
        self.cursor.execute(sql, args) if args else self.cursor.execute(sql)
        self.connection.commit()
        data = self.cursor.fetchall()
        lock.release()
        if data:
            return [list(elt) for elt in data]
    
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
        self.data_path = dirname(abspath(__file__)) + '/Data/'
        self.database_path = self.data_path + "server_database.db"

        if not exists(self.data_path):
            makedirs(self.data_path)

        self.create_database(self.database_path)
        self.create_table("users", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_uid TEXT, username TEXT, public_key TEXT, verification INTEGER, invite_word TEXT")
        self.create_table("invite_keys", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_uid TEXT, invite_hash TEXT")
        self.create_table("accessories", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_uid TEXT, chat TEXT, role TEXT")
        self.create_table("queue", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, data TEXT, user_uid TEXT")
        self.create_table("related_users", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user TEXT, friend TEXT")
        self.create_chat("server_main", "server")

    #Chat
    def create_chat(self, chat_name, user_uid):
        table = get_cn(chat_name, b'server')
        if not table in self.table_list():
            self.insert("accessories", "user_uid, chat, role", (user_uid, chat_name, "owner"))
            self.create_table(table, "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, send_messages INTEGER, send_media INTEGER, send_s_a_g INTEGER, send_polls INTEGER, embed_links INTEGER, add_users INTEGER, pin_messages INTEGER, change_chat_info INTEGER")
            self.insert(table, "send_messages, send_media, send_s_a_g, send_polls, embed_links, add_users, pin_messages, change_chat_info", (True, True, True, True, True, True, True, True))
            return True
        else:
            return False
    
    def remove_chat(self, chat_name):
        table = get_cn(chat_name, b'server')
        if table in self.table_list():
            self.delete_table(table)
            self.query('DELETE FROM accessories WHERE chat = ?;', (chat_name,))
            return True
        else:
            return False
    
    def update_chat_settings(self, chat_name, args):
        chat_name = get_cn(chat_name, b'server')
        if chat_name in self.table_list():
            self.update(chat_name, "send_messages, send_media, send_s_a_g, send_polls, embed_links, add_users, pin_messages, change_chat_info", args + [1])
            return True
        else:
            return False
    
    def get_chat_settings(self, chat_name):
        chat_name = get_cn(chat_name, b'server')
        return self.query('SELECT * FROM %s;' % (chat_name,))[0]
    
    def join_to_chat(self, chat_name, user):
        query = normalize(self.query('SELECT user_uid FROM accessories WHERE chat = ?', (chat_name,)))
        if not user in query:
            self.insert("accessories", "user_uid, chat, role", (user, chat_name, "user"))
            return True
        else:
            return False
    
    def leave_chat(self, chat_name, user_uid):
        self.query('DELETE FROM accessories WHERE chat = ? AND user_uid = ?;', (chat_name, user_uid))
        return True
    
    def get_chats_like(self, query):
        result = self.query('SELECT chat FROM accessories WHERE chat LIKE ?;', ('%'+query+'%',))
        return normalize(result) if result else None
    
    def get_user_chats(self, user_uid):
        return normalize(self.query('SELECT chat FROM accessories WHERE user_uid = ?', (user_uid,)))
    
    def get_chatlist(self):
        result = self.query('SELECT chat FROM accessories;')
        return normalize(result) if result else None
    
    def get_users_in_chat(self, chat_name):
        return normalize(self.query('SELECT user_uid FROM accessories WHERE chat = ?;', (chat_name,)))
    
    def get_all_users(self):
        query = self.query('SELECT user_uid FROM accessories;')
        return normalize(query) if query else None
    
    #User
    def get_user_uid(self, username):
        return self.query('SELECT user_uid FROM users WHERE username = ?;', (username,))[0]
    
    def get_username(self, user_uid):
        return self.query('SELECT username FROM users WHERE user_uid = ?;', (user_uid,))[0]
    
    def find_user(self, username):
        result = self.query('SELECT username, user_uid FROM users WHERE username = ?;', (username,))
        return normalize(result) if result else None
    
    def get_uid(self, username):
        return self.query('SELECT id FROM users WHERE username = ?;', (username,))[0]
    
    def change_username(self, new_username, username):
        self.update("users", "username", (new_username, self.get_uid(username)))
    
    def add_friend(self, my_uid, user_uid):
        self.insert("related_users", "user, friend", (my_uid, user_uid))
    
    def get_friends(self, user_uid):
        result = self.query('SELECT friend FROM related_users WHERE user = ?;', (user_uid,))
        return normalize(result) if result else None
    
    def remove_friend(self, my_uid, user_uid):
        self.query('DELETE FROM related_users WHERE user = ? AND friend = ?;', (my_uid, user_uid))
    
    #Queue
    def add_to_queue(self, data, user_uid):
        self.insert("queue", "data, user_uid", (data, user_uid))
    
    def remove_from_queue(self, user_uid):
        self.query('DELETE FROM queue WHERE user_uid = ?;', (user_uid,))
    
    def get_user_queue(self, user_uid):
        query = self.query('SELECT data FROM queue WHERE user_uid = ?;', (user_uid,))
        return normalize(query) if query else None
    
    def get_queue(self):
        query = self.query('SELECT user_uid FROM queue;')
        return normalize(query) if query else None


    def __generate_key(self, length):
        return ''.join(choice(ascii_letters + digits + punctuation) for i in range(length))

    def is_user_already_exist(self, user_uid):
        return len(self.find("users", "user_uid", user_uid)) > 0
    
    def is_user_verificated(self, user_uid):
        return self.find("users", "user_uid", user_uid)[0][4] == 1
    
    def is_keys_match(self, user_uid, public_key):
        return public_key in self.find("users", "user_uid", user_uid)[0]
        
    def is_invite_hash_match(self, user_uid, invite_hash):
        return self.find("invite_keys", "user_uid", user_uid)[0][2] == invite_hash
    
    def get_user_id(self, table_name, user_uid):
        return self.find(table_name, "user_uid", user_uid)[0][0]
    
    def make_hash(self, string):
        return sha256(string.encode()).hexdigest()
    
    def add_user_without_verification(self, username, user_uid, public_key):
        self.insert("users", "user_uid, username, public_key, verification", (user_uid, username, public_key, True))
    
    def add_user_with_verification(self, username, user_uid, public_key):
        word = self.__generate_key(32)
        self.insert("users", "user_uid ,username, public_key, verification, invite_word", (user_uid, username, public_key, False, word))
        invite_hash = sha256(word.encode()).hexdigest()
        self.insert("invite_keys", "user_uid, invite_hash", (user_uid, invite_hash))
    
    def verificate_user(self, user_uid, invite_hash):
        if self.is_invite_hash_match(user_uid, invite_hash):
            self.update("users", "verification", [True, self.get_user_id("users", user_uid)])
            self.update("invite_keys", "invite_hash", ['VERIFICATED', self.get_user_id("invite_keys", user_uid)])
            return True
        else:
            return False

class ServerSettings:
    def __init__(self):
        self.config = ConfigParser()
        self.config_path = 'config.ini'
        self.server_ip = '0.0.0.0'
        self.server_port = 9191
        self.server_name = 'ptg server'
        self.maximum_users = 100
        self.enable_password = False
        self.protocol = Protocol()
        self.database = ServerDatabase()

        if isfile(self.config_path):
            if not isfile("private.pem"):
                self.save_key(RSACrypt().export_private())
            self.load()
        else:
            self.save()

    def encrypt_key(self, key, user_key):
        return RSACrypt().encrypt(key, user_key)

    def save(self):
        self.config["NET"] = {"server_ip" : self.server_ip, "server_port" : self.server_port}
        self.config["SETTINGS"] = {"server_name": self.server_name, "max_slots" : self.maximum_users, "enable_password" : self.enable_password}

        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)
    
    def getlist(self, string):
        return (''.join(i for i in string if not i in ['[', ']', '\'', ' '])).split(',')
    
    def load_key(self):
        with open('private.pem', "rb") as pem_file:
            return AESCrypt(sha256(self.server_ip.encode()).hexdigest()).decrypt(pem_file.read())

    def save_key(self, private_key):
        with open('private.pem', "wb") as pem_file:
            key = AESCrypt(sha256(self.server_ip.encode()).hexdigest()).encrypt(private_key)
            pem_file.write(key)

    def load(self):
        self.config.read(self.config_path)
        self.server_ip = self.config["NET"].get("server_ip")
        self.server_port = self.config["NET"].getint("server_port")
        self.server_name = self.config["SETTINGS"].get("server_name")
        self.maximum_users = self.config["SETTINGS"].getint("max_slots")
        self.enable_password = self.config["SETTINGS"].getboolean('enable_password')
        private_key = self.load_key()
        self.protocol.load_rsa(private_key)

if __name__ == "__main__":
    db = ServerDatabase()
    print({data: db.get_chat_settings(data) for data in db.get_user_chats("7aaea446b8ca0712a52c8db346dab5f8399b429c1d560cdfa725ebb2726096b1")})
    print(db.get_chat_settings("server_main"))