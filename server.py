#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
import json
from protocol import Protocol

STATE_READY = 0
STATE_WORKING = 1
STATE_STOPPING = 3

class ServerSettings:
    def __init__(self):
        self.server_ip = '0.0.0.0'
        self.server_port = 9191
        self.maximum_users = 100
        self.server_rooms = ['guest' ,'proggers', 'russian', 'pole']

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
        while self.state == STATE_WORKING and getattr(thread, "do_run", True):
            try:
                data = self.protocol.recv(self.connections[client_index][0])  # Читаем клиент
                if not data == None and "server" in data.decode('utf-8'):
                    self.parse_command(data.decode('utf-8'), client_index)
                    continue

            except s.error as e:
                if e.errno == s.errno.ECONNRESET:
                    print(str(self.connections[client_index][1][0]) + ':' + str(self.connections[client_index][1][1]), "disconnected", len(self.connections))
                    self.connections[client_index][0].close()
                    self.connections.pop(client_index)
                    break
                else:
                    print(e)
                    raise
            
            for connection in self.connections:
                if connection[2] == self.connections[client_index][2] and connection != self.connections[client_index]:
                    self.protocol.send(data, connection[0])  # Отправляем всем клиентам в этой же комнате
    
    def parse_command(self, data, client_index):
        args = data.split(' ')
        command = args[1]
        if command == 'chroom':
            self.change_room(args[2], client_index)

    def change_room(self, room_id, client_index):
        if room_id in self.setting.server_rooms:
            last = self.connections[client_index]
            self.connections[client_index] = [last[0], last[1], room_id]
            print('User moved to %s.' % room_id)
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
        print("Stopping server...")
        self.state = STATE_STOPPING
        for thread in self.threads:
            thread.do_run = False
            thread.join()


if __name__ == "__main__":
    srv = Server()
    srv.run()
