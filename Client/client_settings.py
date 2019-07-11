from os import makedirs
from os.path import dirname, exists, abspath, isfile
from json import load, dump
from protocol import Protocol, RSACrypt, AESCrypt
from hashlib import sha256
from csv import reader, writer

#This class contains all client settings
#- loads settings from file
#- saves settings to file

class Response:
    def __init__(self, recv):
        self.recv = recv

    def response(self):
        if not self.recv:
            return "empty_response"
        else:
            self.recv = self.recv.decode('utf-8')
            if self.recv == "verificalion":
                return "verificalion_response"


class ClientSetting:
    def __init__(self, args=None):
        self.config_path = dirname(abspath(__file__)) + '/config/'
        self.log_path = dirname(abspath(__file__)) + '/Log/'
        self.server_public_key = b''
        self.aes_session_key = b''
        self.nickname = ''
        self.password = ''
        self.server_ip = ''
        self.port = 9191
        self.protocol = Protocol()
        
        if not exists(self.config_path):
            makedirs(self.config_path)
        if not exists(self.log_path):
            makedirs(self.log_path)
    
    def generate_rsa(self):
        self.private_key = RSACrypt().export_private()
    
    def add_new_configuration(self):
        with open('%s/server_list.csv' % self.config_path, "a+") as file:
            readed = file.read().split(',')
            new_line = '%s%s:%s' % (',' if len(readed) > 0 else '' ,self.server_ip, self.port)
            if not new_line in readed:
                file.write(new_line)
    
    def load_configurations(self):
        with open('%s/server_list.csv' % self.config_path, "r") as file:
            return file.read()
    
    def load_last_configuration(self):
        with open('%s/server_list.csv' % self.config_path, "r") as file:
            lines = file.read()
            return lines[len(lines)-1]

    def load(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        with open('%s/%s.json' % (self.config_path, config_hash) , "r") as read_f:
            data = load(read_f)
            self.nickname = data["nickname"]
            self.password = data["password"]
            self.server_ip = data["ip"]
            self.port = data["port"]
    
    def load_key(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        with open('%s/%s.pem' % (self.config_path, config_hash), "rb") as pem_file:
            private_key = AESCrypt(sha256(self.password.encode('utf-8')).hexdigest()).decrypt(pem_file.read())
            self.protocol.load_rsa(private_key)
            self.RSA = self.protocol.RSA

    def save_key(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        if not isfile('%s/%s.pem' % (self.config_path, config_hash)):
            with open('%s/%s.pem' % (self.config_path, config_hash), "wb") as pem_file:
                key = AESCrypt(sha256(self.password.encode('utf-8')).hexdigest()).encrypt(self.private_key)
                pem_file.write(key)

    def save(self):
        self.add_new_configuration()
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        with open('%s/%s.json' % (self.config_path, config_hash), "w") as write_f:
            data = {"nickname" : self.nickname ,"password" : self.password,
            "ip" : self.server_ip, "port" : self.port}
            dump(data, write_f)
            self.save_key()