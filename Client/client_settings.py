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
        self.config_path = 'config/user.conf'
        self.server_public_key = b''
        self.aes_session_key = b''

        self.config_dir = dirname(abspath(self.config_path))
        if not exists(self.config_dir):
            makedirs(self.config_dir)
        
        if isfile(self.config_path) and not args: 
            self.load()
        else:
            self.username = args[0]
            self.nickname = args[1]
            self.password = args[2]
            self.private_key = RSACrypt().export_private()
            self.server_ip = args[3]
            self.port = args[4]
            self.save()
    
    def update_rca(self):
        self.private_key = RSACrypt().export_private()
        self.save_key()
        self.private_key = self.load_key()

    def load(self):
        with open(self.config_path, "r") as read_f:
            data = load(read_f)
            self.username = data["username"]
            self.nickname = data["nickname"]
            self.password = data["password"]
            self.private_key = self.load_key()
            self.server_ip = data["ip"]
            self.port = data["port"]
            self.RSA = RSACrypt(self.private_key)
            self.public_key = self.RSA.export_public()
    
    def load_key(self):
        with open('%s/private.pem' % self.config_dir, "rb") as pem_file:
            return AESCrypt(sha256(self.password.encode('utf-8')).hexdigest()).decrypt(pem_file.read())

    def save_key(self):
        with open('%s/private.pem' % self.config_dir, "wb") as pem_file:
            key = AESCrypt(sha256(self.password.encode('utf-8')).hexdigest()).encrypt(self.private_key)
            pem_file.write(key)

    def save(self):
        with open(self.config_path, "w") as write_f:
            data = {"username" : self.username ,"nickname" : self.nickname ,"password" : self.password,
            "ip" : self.server_ip, "port" : self.port}
            self.save_key()
            dump(data, write_f)