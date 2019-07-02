#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
from protocol import Protocol
from autologging import logged, traced
from server_database import ServerDatabase, ServerSettings
from exceptions import LoginError

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
        self.public_key = 'hello_world_mf'

    def handler(self, client_index):
        thread = threading.current_thread()
        while self.state == STATE_WORKING and getattr(thread, "do_run", True):
            try:
                data = self.protocol.recv(self.connections[client_index][0])  # Читаем клиент
                self.parse_client_command(data, client_index)
                self_data = self.connections[client_index]
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
    
    def verificate(self, username, connection):
        try:
            data = self.protocol.recv(connection[0]).decode('utf-8')
        except Exception:
            print('Client lost connection.')
            return False
            
        return True if self.server_database.verificate_user(username, data) else False

    def signup(self, data, connection):
        username = data[0]
        password = data[1]
        if self.setting.enable_password:
            self.server_database.add_user_with_verification(username, password)
            if self.verificate(username, connection):
                return True
            else:
                return False
        else:
            self.server_database.add_user_without_verification(username, password)
            return True
    
    def signin(self, data, connection):
        if isinstance(data, (bytes, bytearray)):
            username, password = data.decode('utf-8').split(',')
        else:
            username, password = data[0], data[1]
        if self.server_database.is_user_already_exist(username):
            if self.server_database.is_user_verificated(username):
                if self.server_database.is_passwords_match(username, password):
                    #success connection
                    return True
                else:
                    #raise LoginError("Passwords not match.")
                    return False
            else:
                if self.verificate(username, connection):
                    self.signin([username, str(password)], connection)
                    return True
                else:
                    #raise LoginError("Varification error.")
                    return False
        else:
            if self.signup([username, str(password)], connection):
                self.signin([username, str(password)], connection)
                return True
            else:
                #raise LoginError("Unknown error.")
                return False


    def parse_client_command(self, data, client_index):
        try:
            string_data = data.decode('utf-8')
        except Exception:
            return
        if not data == None and "server" in string_data:
            args = data.decode('utf-8').split(' ')
            if len(args) > 1:
                command = args[1]
                if command == 'rooms':
                    self.protocol.send(','.join(self.setting.server_rooms), self.connections[client_index][0])
                    return
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
            for connection in self.connections:
                if connection[2] == room_id:
                    self.protocol.send("%s connected to room %s." % (self.connections[client_index][1][0], room_id), connection[0])
        else:
            self.protocol.send('Room %s not found.' % room_id, self.connections[client_index][0])

    def connect(self, client_data):
        if self.signin(self.protocol.recv(client_data[0]), client_data):
            self.protocol.send(self.public_key, client_data[0])
            self.connections.append(client_data)
            self_index = self.connections.index(client_data)

            self.threads.append(threading.Thread(target=self.handler, args=[self_index]))  # Отдельный поток для хандлера
            self.threads[len(self.threads) - 1].daemon = True
            self.threads[len(self.threads) - 1].start()
            print(str(client_data[1][0]) + ':' + str(client_data[1][1]), "connected", len(self.connections))
        else:
            print('Connection denied.')
            client_data[0].close()

    def run(self):
        self.state = STATE_WORKING
        while self.state == STATE_WORKING:
            c, a = self.sock.accept()
            room = self.setting.server_rooms[0]
            client_data = [c, a, room]
            autorisation_thread = threading.Thread(target=self.connect, args=[client_data])
            autorisation_thread.start()

            
    
    def stop(self):
        self.state = STATE_STOPPING
        for thread in self.threads:
            thread.do_run = False
            thread.join()