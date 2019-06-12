#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
from threading import Thread
import json, sys, struct, os

#This class contains all slient settings
#- loads settings from file
#- saves settings to file
class ClientSetting:
    def __init__(self):
        self.nickname = 'Jimmy'
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
            self.server_ip = data["ip"]
            self.port = data["port"]
    
    def save(self, fname='config/user.json'):
        if not os.path.exists('config/'):
            os.makedirs('config/')
        with open(fname, "w") as write_f:
            data = {"nickname" : self.nickname, "ip" : self.server_ip, "port" : self.port}
            json.dump(data, write_f)


class Client:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)               #Creating up network socket

    def __init__(self, nickname='Jimmy', address='localhost', port=9191):
        self.version = "alpha"
        self.setting = ClientSetting()
        self.setting.nickname = nickname
        self.setting.server_ip = address
        self.setting.port = port

        self.sock.connect((self.setting.server_ip, self.setting.port))

        thread = Thread(target=self.listen)
        thread.daemon = True
        thread.start()

    def listen(self):
        while True:
            data = self.recv()
            if not data:
                break
            raw_data = json.loads(data)
            print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))
    
    def parse_command(self, string):
        args = string.split(" ")
        for a in args:
            if a == "p":
                print("New password: %s" % args[1])
                break
            elif a == "e":
                self.sock.close()
                exit()
            elif a == "v":
                print(self.version)
                break

        
    
    def send(self, input_msg): #Message sending method
        if(input_msg[0] == "/"):
            self.parse_command(input_msg.split("/")[1])
        else:
            msg_data = {"nickname": self.setting.nickname, "msg": input_msg}
            raw_data = json.dumps(msg_data, ensure_ascii=False).encode('utf-8')
            msg = struct.pack('>I', len(raw_data)) + raw_data
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
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def start(self):
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        clt = Client(sys.argv[1], 'localhost', 9191)
