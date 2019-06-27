#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading, json, os
from protocol import Protocol
from autologging import logged, traced
import logging

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
        self.config_path = 'Server/config.conf'
        self.server_ip = '0.0.0.0'
        self.server_port = 9191
        self.maximum_users = 100
        self.server_rooms = ['guest' ,'proggers', 'russian', 'pole']

        if os.path.isfile(self.config_path):
            self.load()
        else:
            self.save()
    
    def load(self):
        with open(self.config_path, "r") as read_f:
            data = json.load(read_f)
            self.server_ip = data["ip"]
            self.server_port = data["port"]
            self.maximum_users = data["max_users"]
            self.server_rooms = data["rooms"]
    
    def save(self):
        with open(self.config_path, "w") as write_f:
            data = {"ip" : self.server_ip, "port" : self.server_port, "max_users" : self.maximum_users, "rooms" : self.server_rooms}
            json.dump(data, write_f)

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
