#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

from os import makedirs
from os.path import dirname, exists, abspath, isfile
from json import load, dump
from protocol import Protocol, RSACrypt, AESCrypt
from hashlib import sha256
from shutil import rmtree

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
            self.recv = self.recv.decode()
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
    
    def load_configurations(self):
        try:
            with open('%s/server_list.json' % self.config_path, "r") as file:
                return load(file)
        except:
            return None
    
    def set_last(self, configuration):
        confs = self.load_configurations()
        for conf in confs.keys():
            confs[conf] = False
        confs[configuration] = True
        with open('%s/server_list.json' % self.config_path, "w") as file:
            dump(confs, file)
    
    def get_last(self):
        confs = self.load_configurations()
        if confs:
            for conf in confs.keys():
                if confs[conf]:
                    return conf
        else:
            return None

    def add_new_configuration(self):
        if isfile('%s/server_list.json' % self.config_path):
            current = self.load_configurations()
            with open('%s/server_list.json' % self.config_path, "w") as file:
                new_conf = '%s:%s' % (self.server_ip, self.port)
                if not new_conf in current.keys():
                    current.update({new_conf: True})
                dump(current, file)
        else:
            with open('%s/server_list.json' % self.config_path, "w") as file:
                new_conf = '%s:%s' % (self.server_ip, self.port)
                dump({new_conf: True}, file)
        self.set_last(new_conf)

    def remove_configuration(self, configuration):
        current = self.load_configurations()
        conf = configuration.split(':')
        config_hash = sha256((conf[0]+conf[1]).encode()).hexdigest()
        with open('%s/server_list.json' % self.config_path, "w") as file:
            if configuration in current.keys():
                rmtree('%s%s/' % (self.config_path, config_hash))
                current.pop(configuration, None)
                dump(current, file)

    def load(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode()).hexdigest()
        with open('%s/%s/profile.json' % (self.config_path, config_hash) , "r") as read_f:
            data = load(read_f)
            self.nickname = data["nickname"]
            self.password = data["password"]
            self.server_ip = data["ip"]
            self.port = data["port"]
    
    def load_key(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode()).hexdigest()
        with open('%s/%s/prof_key.pem' % (self.config_path, config_hash), "rb") as pem_file:
            private_key = AESCrypt(sha256(self.password.encode()).hexdigest()).decrypt(pem_file.read())
            self.protocol.load_rsa(private_key)
            self.RSA = self.protocol.RSA

    def save_key(self):
        config_hash = sha256((self.server_ip + str(self.port)).encode()).hexdigest()
        if not isfile('%s/%s/prof_key.pem' % (self.config_path, config_hash)):
            with open('%s/%s/prof_key.pem' % (self.config_path, config_hash), "wb") as pem_file:
                key = AESCrypt(sha256(self.password.encode()).hexdigest()).encrypt(self.private_key)
                pem_file.write(key)

    def save(self):
        self.add_new_configuration()
        config_hash = sha256((self.server_ip + str(self.port)).encode()).hexdigest()
        if not exists(self.config_path+config_hash):
            makedirs(self.config_path+config_hash)
        with open('%s/%s/profile.json' % (self.config_path, config_hash), "w") as write_f:
            data = {"nickname" : self.nickname ,"password" : self.password,
            "ip" : self.server_ip, "port" : self.port}
            dump(data, write_f)
            self.save_key()