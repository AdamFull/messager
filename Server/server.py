#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
from protocol import Protocol
from autologging import logged, traced
from Server.server_settings import ServerSettings
from Server.server_database import ServerDatabase

STATE_READY = 0
STATE_WORKING = 1
STATE_STOPPING = 3


@traced
@logged
class Server:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)  # Создаём сетевой сокет
    sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #Это позволяет испольдовать сокет даже если он не был корректно закрыт
    connections = list()  # Лист для хранения всех подключений
    threads = list()

    def __init__(self):
        self.setting = ServerSettings()
        self.server_database = ServerDatabase()

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
                self.parse_client_command(data, client_index)

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
    
    def parse_server_command(self, data):
        if not data == None:
            args = data.split(' ')
    
    def signup(self, data):
        username = data[0]
        password = data[1]
    
    def signin(self, data):
        username = data[0]
        password = data[1]
        if self.server_database.is_user_already_exist(username):
            password_hash = self.make_hash(password)
            if self.server_database.is_user_verificated(username):
                if self.server_database.is_passwords_match(username, password_hash):
                    #success connection
                    return True
                else:
                    raise Error("Passwords not match.")
            else:
                raise Error("User not verificated.")
        else:
            if self.signup([username, password]):
                self.signin([username, password])
            else:
                raise Error("Unknown error.")



    def parse_client_command(self, data, client_index):
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
