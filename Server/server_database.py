from Server.sql_interface import SqlInterface
from os import path, makedirs
from hashlib import sha256

class ServerDatabase(SqlInterface):
    def __init__(self):
        self.data_path = 'Server/Data/'
        self.database_path = self.data_path + "server_database.db"

        if not path.exists(self.data_path):
            makedirs(self.data_path)

        self.create_database(self.database_path)
        self.create_table("users", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, password TEXT, verification INTEGER, invite_word TEXT")
        self.create_table("invite_keys", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, invite_hash TEXT")

    def is_user_already_exist(self, username):
        return True if len(self.find("users", "username", username)) > 0 else False
    
    def is_user_verificated(self, username):
        return True if True in self.find("users", "username", username)[0] else False
    
    def is_passwords_match(self, username, password_hash):
        return True if password_hash in self.find("users", "username", username)[0] else False
        
    def is_invite_hash_match(self, invite_hash):
        return True if len(self.find("invite_keys", "invite_hash", invite_hash)) > 0 else False
    
    def add_user_without_verification(self, username, password):
        password_hash = sha256(password.encode('utf-8')).hexdigest()
        self.insert("users", "username, password, verification", (username, password, True))
    
    def add_user_with_verification(self, username, password):
        pass
