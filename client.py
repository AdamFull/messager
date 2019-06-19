#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
import json, sys, struct, os
import encryption
from Crypto.PublicKey import RSA

#This class contains all client settings
#- loads settings from file
#- saves settings to file
class ClientSetting:
    def __init__(self):
        self.nickname = 'Jimmy'
        self.password = 'password'
        self.server_ip = 'localhost'
        self.port = 9191
        #and so on

        if os.path.exists('config/'):
            if os.path.exists('config/user.dat'): 
                self.load()   

    def load(self, fname='config/user.dat'):
        with open(fname, "r") as read_f:
            data = json.load(read_f)
            self.nickname = data["nickname"]
            self.password = data["password"]
            self.server_ip = data["ip"]
            self.port = data["port"]
    
    def save(self, fname='config/user.dat'):
        if not os.path.exists('config/'):
            os.makedirs('config/')
        with open(fname, "w") as write_f:
            data = {"nickname" : self.nickname, "password" : self.password, "ip" : self.server_ip, "port" : self.port}
            json.dump(data, write_f)


class Client:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)
    def __init__(self, nickname='Jimmy', address='localhost', port=9191):
        self.setting = ClientSetting()
        self.setting.nickname = nickname
        self.setting.server_ip = address
        self.setting.port = port

        self.threads = list()

        self.isConnected = False

        self.connect(self.setting.server_ip, self.setting.port)

    def listen(self):
        current_thread = threading.current_thread()
        while getattr(current_thread, "do_run", True):
            data = self.recv()
            if not data:
                break
            raw_data = json.loads(self.crypto.decrypt(data))
            print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))


    def connect(self, ip=None, port=None):
        if not ip or not port:
            print("Connecting to last server.")
            self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.sock.connect((self.setting.server_ip, self.setting.port))
            print("Connected to %s:%s" % (self.setting.server_ip, self.setting.port))
            return
        if self.isConnected:
            print("Allready connected to: %s:%s" % (self.setting.server_ip, self.setting.port))
            return None

        print("Connecting to %s:%s" % (ip, port))
        try:
            self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.sock.connect((ip, port))
        except Exception as e:
            print("Connection error. %s" % e)
            return None
        self.key = self.recv()
        self.crypto = encryption.AESCrypt(self.key)

        self.setting.server_ip = ip
        self.setting.port = port

        print("Connected to %s:%s" % (ip, port))
        self.isConnected = True
        self.threads.append(threading.Thread(target=self.listen))
        self.threads[0].daemon = True
        self.threads[0].do_run = True
        self.threads[0].start()
    
    def disconnect(self):
        print("Disconnecting from server.")
        self.isConnected = False
        self.threads[0].do_run = False
        self.sock.close()
        self.threads[0].join()
        self.threads.clear()
        
        
    
    def send(self, input_msg): #Message sending method
        msg_data = {"nickname": self.setting.nickname, "msg": input_msg}
        raw_data = json.dumps(msg_data, ensure_ascii=False).encode('utf-8')
        crypted = self.crypto.encrypt(raw_data)
        msg = struct.pack('>I', len(crypted)) + crypted
        self.sock.sendall(msg)
    
    def recv(self): #Message receiving method
        raw_msglen = self.recvall(4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.recvall(msglen)

    def recvall(self, n): #Вспомогательный метод для принятия сообщений, читает из сокета
        data = b''
        while len(data) < n:
            try:
                packet = self.sock.recv(n - len(data))
            except Exception as e:
                print("Server lost connection.")
                return None
            if not packet:
                return None
            data += packet
        return data

    def start(self):
        pass
    
    def set_password(self, new_password):
        self.setting.password = new_password
        self.setting.save()
    
    def close(self):
        self.setting.save()
        self.sock.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        clt = Client(sys.argv[1], 'localhost', 9191)
