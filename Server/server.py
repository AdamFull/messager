#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading, json, os, configparser
from protocol import Protocol
from autologging import logged, traced
import logging
from hashlib import sha256

STATE_READY = 0
STATE_WORKING = 1
STATE_STOPPING = 3

@traced
@logged
class ServerData:
    def __init__(self):
        self.data_path = 'Server/Data/'
        self.cache_path = 'Server/Cache/'
        
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

@traced
@logged
class ServerSettings:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = 'Server/config.ini'
        self.server_ip = '0.0.0.0'
        self.server_port = 9191
        self.maximum_users = 100
        self.enable_password = False
        self.server_password = '790DFE9491B740FFC9131B2283CD72DD557AC7C7F51D12F65AC846ECECCEF9B9' #hello_world
        self.enable_whitelist = False
        self.whitelist = []
        self.server_rooms = ['guest' ,'proggers', 'russian', 'pole']

        if os.path.isfile(self.config_path):
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
        

    def load(self):
        self.config.read(self.config_path)
        self.server_ip = self.config["NET"].get("server_ip")
        self.server_port = self.config["NET"].get("server_port")
        self.maximum_users = self.config["SETTINGS"].get("max_slots")
        self.enable_password = self.config["SETTINGS"].getboolean('enable_password')
        self.server_password = self.config["SETTINGS"].get('server_password')
        self.enable_whitelist = self.config["SETTINGS"].getboolean('enable_whitelist')
        self.whitelist = self.config["SETTINGS"].getlist('white_list')
        self.server_rooms = self.config["SETTINGS"].getlist('rooms')


@traced
@logged
class Server:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)  # Создаём сетевой сокет
    sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #Это позволяет испольдовать сокет даже если он не был корректно закрыт
    connections = list()  # Лист для хранения всех подключений
    threads = list()

    def __init__(self):
        self.setting = ServerSettings()

        self.sock.bind((self.setting.server_ip, self.setting.server_port))  # Задаём параметры сокета
        self.sock.listen(self.setting.maximum_users)  # Слушаем сокет
        self.state = STATE_READY
        self.protocol = Protocol()

    def handler(self, client_index):
        thread = threading.current_thread()
        self_data = self.connections[client_index]
        while self.state == STATE_WORKING and getattr(thread, "do_run", True):
            try:
                data = self.protocol.recv(self.connections[client_index][0])  # Читаем клиент
                self.parse_command(data, client_index)

            except s.error as e:
                if e.errno == s.errno.ECONNRESET:
                    slef_index = self.connections.index(self_data)
                    print(str(self.connections[slef_index][1][0]) + ':' + str(self.connections[slef_index][1][1]), "disconnected", len(self.connections))
                    self.connections[slef_index][0].close()
                    self.connections.pop(slef_index)
                    break
                else:
                    print(e)
                    raise
            
            for connection in self.connections:
                if connection[2] == self.connections[client_index][2] and connection != self.connections[client_index]:
                    self.protocol.send(data, connection[0])  # Отправляем всем клиентам в этой же комнате
    
    def parse_command(self, data, client_index):
        if not data == None and "server" in data.decode('utf-8'):
            args = data.decode('utf-8').split(' ')
            if len(args) > 2:
                command = args[1]
                if command == 'chroom':
                    self.change_room(args[2], client_index)
            else:
                self.protocol.send("Not Enought arguments.",self.connections[client_index][0])

    def change_room(self, room_id, client_index):
        if room_id in self.setting.server_rooms:
            last = self.connections[client_index]
            self.connections[client_index] = [last[0], last[1], room_id]
        else:
            self.protocol.send('Room %s not found.' % room_id, self.connections[client_index][0])

    def run(self):
        self.state = STATE_WORKING
        while self.state == STATE_WORKING:
            c, a = self.sock.accept()
            room = self.setting.server_rooms[0]
            client_data = [c, a, room]
            self.connections.append(client_data)
            self_index = self.connections.index(client_data)

            self.threads.append(threading.Thread(target=self.handler, args=[self_index]))  # Отдельный поток для хандлера
            self.threads[len(self.threads) - 1].daemon = True
            self.threads[len(self.threads) - 1].start()
            print(str(a[0]) + ':' + str(a[1]), "connected", len(self.connections))
    
    def stop(self):
        self.state = STATE_STOPPING
        for thread in self.threads:
            thread.do_run = False
            thread.join()


if __name__ == "__main__":
    srv = Server()
    srv.run()
