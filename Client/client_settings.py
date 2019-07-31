import sqlite3
from os import makedirs
from os.path import dirname, exists, abspath, isfile
from json import load, dump
from protocol import Protocol, RSACrypt, AESCrypt
from hashlib import sha256
from shutil import rmtree

#This class contains all client settings
#- loads settings from file
#- saves settings to file

sha_hd = lambda x: sha256(x.encode()).hexdigest()
sha_d = lambda x: sha256(x.encode()).digest()
get_cn = lambda x, y: "chat%s" % sha256(x.encode() + y.exportKey()).hexdigest()

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
        self.cursor.execute(sql, args) if args else self.cursor.execute(sql)
        self.connection.commit()
        data = self.cursor.fetchall()
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

class ClientDatabase(SqlInterface):
    def __init__(self, configuration: list = None):
        self.config_path = dirname(abspath(__file__)) + '/config/'
        self.log_path = dirname(abspath(__file__)) + '/Log/'
        self.database_path = "%sdatabase.db" % self.config_path

        makedirs(self.config_path) if not exists(self.config_path) else None
        makedirs(self.log_path) if not exists(self.log_path) else None

        self.create_database(self.database_path)
        self.create_table("user_settings", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, server_ip TEXT, server_port INTEGER, nickname TEXT, password TEXT, private_key TEXT")

        self.nickname = None
        self.password = None
        self.server_ip = None
        self.server_port = None
        self.protocol = Protocol()

        self.load(configuration) if configuration else None

    def load(self, configuration):
        conf = configuration
        settings = self.query('SELECT * FROM user_settings WHERE "server_ip" = ? AND "server_port" = ? AND "nickname" = ?;', conf[:len(conf)-1])
        if settings:
            settings = settings[0]
            self.server_ip = settings[1]
            self.server_port = settings[2]
            self.nickname = settings[3]
            self.password = settings[4]
            private_key = AESCrypt(sha_hd(self.password)).decrypt(settings[5])
            self.protocol.load_rsa(private_key)
        else:
            private_key = RSACrypt().export_private()
            private_key = AESCrypt(sha_hd(conf[3])).encrypt(private_key)
            conf.append(private_key)
            self.insert("user_settings", "server_ip, server_port, nickname, password, private_key", conf)
            self.load(conf[:len(conf)-1])
    
    def get_configurations(self):
        return self.query('SELECT * FROM user_settings;')

    def load_last(self):
        settings = self.query('SELECT * FROM user_settings WHERE "is_last" = ?', True)
    
    def join_to_chat(self, chat_name):
        chat_name = get_cn(chat_name, self.protocol.public_rsa_key)
        self.create_table(chat_name, "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, message TEXT, chat TEXT, time TEXT, data TEXT")
    
    def load_chat(self, chat_name):
        chat_name = get_cn(chat_name, self.protocol.public_rsa_key)
        result = self.query('SELECT * FROM %s' % chat_name)
        return result
    
    def chat_exists(self, chat_name):
        chat_name = get_cn(chat_name, self.protocol.public_rsa_key)
        return True if chat_name in self.table_list() else False

    def recv_message(self, chat_name, data):
        chat_name = get_cn(chat_name, self.protocol.public_rsa_key)
        self.insert(chat_name, "username, message, chat, time, data", (data["nickname"], data["msg"], data["chat"], data["time"], data["date"]))

if __name__ == "__main__":
    config =  ["localhost", 9191, "nagibator2281112", "g159753159754H"]
    database = ClientDatabase(config)