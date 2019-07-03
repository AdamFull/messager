#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
from os import system
from json import dumps, loads
from protocol import Protocol
from autologging import logged, traced
from hashlib import sha256
from encryption import AESCrypt, RSACrypt
from client_settings import ClientSetting

class STATEMENT:
    def __init__(self):
        self.DISCONNECTED = 0
        self.CONNECTING = 1
        self.CONNECTED = 2
        self.VERIFICATION = 3

@traced
@logged
class Client:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)
    def __init__(self, receive_callback=None):
        self.setting = ClientSetting()

        self.STATE = STATEMENT().DISCONNECTED
        self.current_message = ''

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
                system('cls')
                self.current_message = 'Current connection: none.'
                break
            if self.iscrypted(data):
                raw_data = loads(self.crypto.decrypt(data))
                if self.rcv_output:
                    self.rcv_output(raw_data)
                else:
                   self.current_message = "[%s]: %s" % (raw_data["nickname"], raw_data["msg"])
            else:
                self.current_message = data.decode('utf-8')

    def login(self):
        self.protocol.send("wanna_connect", self.sock) # Sending connection request to server.
        while True:
            response = self.protocol.recv(self.sock)
            if response:
                response = response.decode('utf-8')
                if response == "success":
                    login_result = self.protocol.recv(self.sock)
                    self.setting.aes_session_key = self.setting.RSA.decrypt(login_result.decode('utf-8'))
                    self.crypto = AESCrypt(self.setting.aes_session_key)
                    return True
                elif response == "verification":
                    self.STATE = STATEMENT().VERIFICATION
                    #self.send_verification_key(input("Verification key: "))
                elif response == "key_error":
                    self.current_message = "Keys don't match"
                    return False
                elif response == "userdata":
                    self.protocol.send(','.join([self.setting.username, self.setting.public_key.decode('utf-8')]), self.sock)
                elif response == "server_puplic_key":
                    self.setting.server_public_key = self.protocol.recv(self.sock).decode('utf-8') # Waiting server public rsa key.
                else:
                    return False
            
            else:
                if self.STATE == STATEMENT().VERIFICATION:
                    self.current_message = "Waiting varification key."
                else:
                    self.current_message = "Waiting server response."
                continue
        return False
        
        
    
    def send_verification_key(self, key):
        key_hash = sha256(key.encode('utf-8')).hexdigest()
        self.protocol.send(key_hash, self.sock)

    def connect(self, ip, port, attempts = 5):
        if self.STATE == STATEMENT().CONNECTED:
            self.current_message = "Allready connected to: %s:%s" % (self.setting.server_ip, self.setting.port)
            return False
        self.STATE = STATEMENT().CONNECTING
        self.current_message = "Trying to connect: %s:%s" % (ip, port)
        try:
            self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.sock.connect((ip, port))
        except Exception as e:
            if attempts > 0:
                attempt = attempts-1
                return self.connect(ip, port, attempt)
            else:
                self.current_message = 'Connection failed.'
                return False
        self.setting.server_ip = ip
        self.setting.port = port

        self.protocol = Protocol()

        if self.login():
            self.isLogined = True
            system('cls')
            self.current_message = "Current connection: %s:%s" % (ip, port)
            self.STATE = STATEMENT().CONNECTED
            self.threads.append(threading.Thread(target=self.listen))
            self.threads[0].daemon = True
            self.threads[0].do_run = True
            self.threads[0].start()
            return True
        else:
            return False
    
    def disconnect(self):
        self.current_message = "Disconnecting from server."
        self.STATE = STATEMENT().DISCONNECTED
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
        raw_data = self.crypto.encrypt(dumps(msg_data, ensure_ascii=False).encode('utf-8'))
        self.protocol.send(raw_data, self.sock)
        

    def start(self):
        pass
    
    def set_password(self, new_password):
        self.setting.password = new_password
        self.setting.save()
    
    def close(self):
        self.sock.detach()