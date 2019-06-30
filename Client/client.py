#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading, json, os, logging
from protocol import Protocol
from autologging import logged, traced
from hashlib import sha256
from encryption import AESCrypt

#This class contains all client settings
#- loads settings from file
#- saves settings to file
@traced
@logged
class ClientSetting:
    def __init__(self):
        self.config_path = 'config/user.conf'
        self.username = 'Jonh'
        self.nickname = 'Wick'
        self.password = 'password'
        self.server_ip = 'localhost'
        self.port = 9191
        #and so on
        self.config_dir = os.path.dirname(os.path.abspath(self.config_path))
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        if os.path.isfile(self.config_path): 
            self.load()
        else:
            self.save()

    def load(self):
        with open(self.config_path, "r") as read_f:
            data = json.load(read_f)
            self.username = data["username"]
            self.nickname = data["nickname"]
            self.password = data["password"]
            self.server_ip = data["ip"]
            self.port = data["port"]
    
    def save(self):
        with open(self.config_path, "w") as write_f:
            data = {"username" : self.username, "nickname" : self.nickname ,"password" : self.password, "ip" : self.server_ip, "port" : self.port}
            json.dump(data, write_f)

@traced
@logged
class Client:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)
    def __init__(self, receive_callback=None):
        self.setting = ClientSetting()

        self.threads = list()

        #This callback sets by frontend to handle incoming messages
        self.rcv_output = receive_callback

        self.isConnected = False
        self.isLogined = False

    def iscrypted(self, data):
        try:
            data.decode('utf-8')
            return False
        except Exception:
            return True

    def listen(self):
        current_thread = threading.current_thread()
        while getattr(current_thread, "do_run", True):
            try:
                data = self.protocol.recv(self.sock)

            except Exception:
                os.system('cls')
                print('Current connection: none.')
                break

            if self.iscrypted(data):
                raw_data = json.loads(self.crypto.decrypt(data))
                if self.rcv_output:
                    self.rcv_output(raw_data)
                else:
                    print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))
            else:
                print(data.decode('utf-8'))

    def login(self, username, password):
        print("Start login in.")
        self.protocol.send(','.join([username, sha256(password.encode('utf-8')).hexdigest()]), self.sock)

        try:
            login_result = self.protocol.recv(self.sock)
        except Exception:
            print('Server lost connection.')
            return False
        self.crypto = AESCrypt(login_result)
        return True
        
    
    def send_verification_key(self, key):
        key_hash = sha256(key.encode('utf-8')).hexdigest()
        self.protocol.send(key_hash, self.sock)

    def connect(self, ip, port, attempts = 5):
        if self.isConnected:
            print("Allready connected to: %s:%s" % (self.setting.server_ip, self.setting.port))
            return False

        print("Trying to connect: %s:%s" % (ip, port))
        try:
            self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.sock.connect((ip, port))
        except Exception as e:
            if attempts > 0:
                attempt = attempts-1
                return self.connect(ip, port, attempt)
            else:
                print('Connection failed.')
                return False
        self.setting.server_ip = ip
        self.setting.port = port

        self.protocol = Protocol()

        if self.login(self.setting.username, self.setting.password):
            self.isLogined = True
            os.system('cls')
            print("Current connection: %s:%s" % (ip, port))
            self.isConnected = True
            self.threads.append(threading.Thread(target=self.listen))
            self.threads[0].daemon = True
            self.threads[0].do_run = True
            self.threads[0].start()
            return True
        else:
            return False
    
    def disconnect(self):
        print("Disconnecting from server.")
        self.isConnected = False
        self.isLogined = False
        self.threads[0].do_run = False
        self.sock.close()
        self.threads[0].join()
        self.threads.clear()
    
    def run(self):
        self.connect(self.setting.server_ip, self.setting.port)
    
        
    def server_command(self, command):
        self.protocol.send(command, self.sock)
    
    def send(self, input_msg): #Message sending method
        msg_data = {"nickname": self.setting.nickname, "msg": input_msg}
        raw_data = self.crypto.encrypt(json.dumps(msg_data, ensure_ascii=False).encode('utf-8'))
        self.protocol.send(raw_data, self.sock)
        

    def start(self):
        pass
    
    def set_password(self, new_password):
        self.setting.password = new_password
        self.setting.save()
    
    def close(self):
        self.sock.close()