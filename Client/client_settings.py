from os import makedirs
from os.path import dirname, exists, abspath, isfile
from json import load, dump
from encryption import RSACrypt, AESCrypt
from hashlib import sha256

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
        self.private_key = b''
        self.public_key = b''
        self.username = ''
        self.nickname = ''
        self.password = ''
        self.server_ip = ''
        self.port = 9191
        print("Создай ещё файл с айпишниками, чтобы была возможность выбирать сервер.")
        
        if not exists(self.config_path):
            makedirs(self.config_path)
        if not exists(self.log_path):
            makedirs(self.log_path)
    
    def generate_rsa(self):
        self.private_key = RSACrypt().export_private()

    def load(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        with open('%s/%s.json' % (self.config_path, config_hash) , "r") as read_f:
            data = load(read_f)
            self.username = data["username"]
            self.nickname = data["nickname"]
            self.password = data["password"]
            self.server_ip = data["ip"]
            self.port = data["port"]
    
    def load_key(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        with open('%s/%s.pem' % (self.config_path, config_hash), "rb") as pem_file:
            self.private_key = AESCrypt(sha256(self.password.encode('utf-8')).hexdigest()).decrypt(pem_file.read())
            self.RSA = RSACrypt(self.private_key)
            self.public_key = self.RSA.export_public()

    def save_key(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        if not isfile('%s/%s.pem' % (self.config_path, config_hash)):
            with open('%s/%s.pem' % (self.config_path, config_hash), "wb") as pem_file:
                key = AESCrypt(sha256(self.password.encode('utf-8')).hexdigest()).encrypt(self.private_key)
                pem_file.write(key)

    def save(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode('utf-8')).hexdigest()
        with open('%s/%s.json' % (self.config_path, config_hash), "w") as write_f:
            data = {"username" : self.username ,"nickname" : self.nickname ,"password" : self.password,
            "ip" : self.server_ip, "port" : self.port}
            dump(data, write_f)
            self.save_key()