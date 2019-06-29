from configparser import ConfigParser
from hashlib import sha256
from os.path import isfile

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

        if isfile(self.config_path):
            self.load()
        else:
            self.save()
    
    def save(self):
        self.config["NET"] = {"server_ip" : self.server_ip, "server_port" : self.server_port}
        self.config["SETTINGS"] = {"max_slots" : self.maximum_users, "enable_password" : self.enable_password, "server_password" : self.server_password, "enable_whitelist" : self.enable_whitelist,
                                   "white_list" : self.whitelist, "rooms" : self.server_rooms}

        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)
    
    def update_password(self, new_password):
        self.server_password = sha256(new_password.encode('utf-8')).hexdigest()
        self.save()
    
    def getlist(self, string):
        return (''.join(i for i in string if not i in ['[', ']', '\'', ' '])).split(',')

    def load(self):
        self.config.read(self.config_path)
        self.server_ip = self.config["NET"].get("server_ip")
        self.server_port = self.config["NET"].getint("server_port")
        self.maximum_users = self.config["SETTINGS"].getint("max_slots")
        self.enable_password = self.config["SETTINGS"].getboolean('enable_password')
        self.enable_whitelist = self.config["SETTINGS"].getboolean('enable_whitelist')
        self.whitelist = self.getlist(self.config["SETTINGS"].get('white_list'))
        self.server_rooms = self.getlist(self.config["SETTINGS"].get('rooms'))