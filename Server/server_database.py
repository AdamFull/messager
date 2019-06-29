from sql_interface import SqlInterface
from os import path, makedirs
from hashlib import sha256
from random import choice
from string import ascii_letters, punctuation, digits

class ServerDatabase(SqlInterface):
    def __init__(self):
        self.data_path = 'Data/'
        self.database_path = self.data_path + "server_database.db"

        if not path.exists(self.data_path):
            makedirs(self.data_path)

        self.create_database(self.database_path)
        self.create_table("users", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, password TEXT, verification INTEGER, invite_word TEXT")
        self.create_table("invite_keys", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, invite_hash TEXT")

    def __generate_key(self, length):
        return ''.join(choice(ascii_letters + digits + punctuation) for i in range(length))

    def is_user_already_exist(self, username):
        return True if len(self.find("users", "username", username)) > 0 else False
    
    def is_user_verificated(self, username):
        return True if self.find("users", "username", username)[0][3] == 1 else False
    
    def is_passwords_match(self, username, password_hash):
        return True if password_hash in self.find("users", "username", username)[0] else False
        
    def is_invite_hash_match(self, invite_hash):
        return True if len(self.find("invite_keys", "invite_hash", invite_hash)) > 0 else False
    
    def get_user_id(self, table_name, username):
        return self.find(table_name, "username", username)[0][0]
    
    def make_hash(self, string):
        return sha256(string.encode('utf-8')).hexdigest()
    
    def add_user_without_verification(self, username, password):
        self.insert("users", "username, password, verification", (username, password, True))
    
    def add_user_with_verification(self, username, password):
        word = self.__generate_key(32)
        self.insert("users", "username, password, verification, invite_word", (username, password, False, word))
        invite_hash = sha256(word.encode('utf-8')).hexdigest()
        self.insert("invite_keys", "username, invite_hash", (username, invite_hash))
    
    def verificate_user(self, username, invite_hash):
        if self.is_invite_hash_match(invite_hash):
            self.update("users", "verification", [True, self.get_user_id("users", username)])
            self.update("invite_keys", "invite_hash", ['VERIFICATED', self.get_user_id("invite_keys", username)])
            return True
        else:
            return False

