#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
import json, sys, struct, os
from protocol import Protocol

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
            if os.path.exists('config/user.json'): 
                self.load()   

    def load(self, fname='config/user.json'):
        with open(fname, "r") as read_f:
            data = json.load(read_f)
            self.nickname = data["nickname"]
            self.password = data["password"]
            self.server_ip = data["ip"]
            self.port = data["port"]
    
    def save(self, fname='config/user.json'):
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
            data = self.protocol.recv(self.sock)
            if not data:
                break
            if data.decode('utf-8')[0] == '{':
                raw_data = json.loads(data)
                print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))
            else:
                print(data)


    def connect(self, ip, port):
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
        self.setting.server_ip = ip
        self.setting.port = port

        self.protocol = Protocol()

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
        
    def server_command(self, command):
        self.protocol.send(command, self.sock)
    
    def send(self, input_msg): #Message sending method
        msg_data = {"nickname": self.setting.nickname, "msg": input_msg}
        raw_data = json.dumps(msg_data, ensure_ascii=False)
        self.protocol.send(raw_data, self.sock)
        

    def start(self):
        pass
    
    def set_password(self, new_password):
        self.setting.password = new_password
        self.setting.save()
    
    def close(self):
        self.sock.detach()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        clt = Client(sys.argv[1], 'localhost', 9191)
