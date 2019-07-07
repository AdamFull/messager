#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
from threading import Thread
from protocol import Protocol
from autologging import logged, traced
from server_database import ServerDatabase, ServerSettings, RSACrypt
from json import loads, dumps
from typing import List
from string import ascii_letters, punctuation, digits
from random import choice

STATE_READY = 0
STATE_WORKING = 1
STATE_STOPPING = 3

class Connection(socket.socket):
    def __init__(self, connection:socket.socket, args):
        super(Connection, self).__init__()
        self.socket: s.socket = connection
        self.status = ''
        self.connection_status = False
        self.ip: str = args[0]
        self.port: int = args[1]
        self.nickname = ''
        self.rsa_public = ''
        self.thread: Thread = None

class Room(object):
    #List[Connection]
    def __init__(self, name, AES):
        super(Room, self).__init__()
        self.name = name
        self.users = list()
        self.protocol = Protocol()
        self.AES = AES
    
    def connect(self, connection:Connection) -> None:
        if not connection in self.users:
            self.users.append(connection)
            self.send("%s connected to chat." % connection.nickname, connection)
    
    def disconnect(self, connection:Connection) -> None:
        if connection in self.users:
            self.send("%s left the chat." % connection.nickname, connection)
            self.users.pop(self.users.index(connection))
    
    def get_users(self):
        return 'INROOM:,'+','.join(user.nickname for user in self.users)            
    
    def send(self, data, client:Connection):
        for connection in self.users:
            if connection != client and client in self.users:
                try:
                    json = loads(data)
                    json = {"nickname": json["nickname"], "msg": json["msg"], "salt": ''.join(choice(ascii_letters+digits+punctuation) for i in range(32))}
                    self.protocol.send(self.AES.encrypt(dumps(json, ensure_ascii=False).encode('utf-8')), connection.socket)
                except Exception:
                    self.protocol.send(data, connection.socket)
            

@traced
@logged
class Server(socket.socket):
    connections = list() # List for contains connections

    def __init__(self):
        super(Server, self).__init__(socket.AF_INET, socket.SOCK_STREAM) # Creating network socket for server
        self.setting = ServerSettings()
        self.server_database = ServerDatabase()

        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # This allows you to use a socket even if it was not properly closed.
        self.bind((self.setting.server_ip, self.setting.server_port))  # Configure server socket
        self.listen(self.setting.maximum_users)  # Listen socket N connections
        self.state = STATE_READY
        self.protocol = Protocol()
        self.rooms = [Room(name, self.setting.AES) for name in self.setting.server_rooms]
        self.aes_key = self.setting.aes_key_

    def __handler(self, client_connection:Connection):
        while self.state == STATE_WORKING and getattr(client_connection.thread, "do_run", True):
            try:
                data = self.protocol.recv(client_connection.socket)  # Читаем клиент
                if self.isCrypted(data):
                    data = self.setting.AES.decrypt(data).decode('utf-8')
                else:
                    self.__parse_client_command(data, client_connection)
                    continue
            except socket.error as e:
                if e.errno == socket.errno.ECONNRESET:
                    print(str(client_connection.nickname), "disconnected", len(self.connections))
                    for room in self.rooms:
                        room.disconnect(client_connection)
                    client_connection.socket.close()
                    self.connections.pop(self.connections.index(client_connection))
                    break
                else:
                    print(e)
                    raise

            for room in self.rooms:
                room.send(data, client_connection)
    def isCrypted(self, data):
        try:
            data.decode('utf-8')
            return False
        except Exception:
            return True
        
    
    def __verificate(self, username, connection:Connection):
        try:
            # We are waiting for the code word from the user
            self.protocol.send("verification", connection.socket)
            data = self.protocol.recv(connection.socket).decode('utf-8')
        except Exception:
            print('Client lost connection.')
            return False
            
        return True if self.server_database.verificate_user(username, data) else False

    # User registration on the server
    def __signup(self, data, connection:Connection):
        username = data[0]
        public_key = data[1]
        if self.setting.enable_password:
            self.server_database.add_user_with_verification(username, public_key)
            if self.__verificate(username, connection):
                return True
            else:
                return False
        else:
            self.server_database.add_user_without_verification(username, public_key)
            return True

    # User authorization on the server
    def _signin(self, connection:Connection, data=None):
        '''This method is responsible for authorizing the client if it was registered,\n 
        and for registering if the client is not found.'''
        if not data:
            if self.protocol.recv(connection.socket).decode('utf-8') == "wanna_connect":
                self.protocol.send("server_puplic_key", connection.socket)
                self.protocol.send(self.setting.public_key, connection.socket)
                self.protocol.send("userdata", connection.socket)
                data = self.protocol.recv(connection.socket)
                username, public_key = data.decode('utf-8').split(',')
        else:
            username, public_key = data[0], data[1]
        
        connection.nickname = username
        connection.rsa_public = public_key

        if self.server_database.is_user_already_exist(username):
            if self.server_database.is_user_verificated(username):
                if self.server_database.is_keys_match(username, public_key):
                    self.protocol.send("success", connection.socket)
                    key = self.setting.encrypt_key(self.aes_key, public_key)
                    self.protocol.send(key, connection.socket)
                    return True
                else:
                    self.protocol.send('key_error', connection.socket)
                    return False
            else:
                if self.__verificate(username, connection):
                    self._signin(connection, [username, str(public_key)])
                    return True
                else:
                    self.protocol.send('verification_error', connection.socket)
                    return False
        else:
            if self.__signup([username, str(public_key)], connection):
                self._signin(connection, [username, str(public_key)])
                return True
            else:
                # Unknown error.
                return False



    def __parse_client_command(self, data, client_data:Connection):
        '''This method is responsible for processing commands from the client.'''
        try:
            string_data = data.decode('utf-8')
        except Exception:
            return False
        if not data == None and "server" in string_data:
            args = data.decode('utf-8').split(' ')
            if len(args) > 1:
                command = args[1]
                if command == 'rooms':
                    self.protocol.send('ROOMS:,'+','.join(self.setting.server_rooms), client_data.socket)
                if command == 'users':
                    self.protocol.send('USERS:,'+','.join(user.nickname for user in self.connections), client_data.socket)
            if len(args) > 2:
                command = args[1]
                if command == 'chroom':
                    self.__change_room(args[2], client_data)
            return True

    def __change_room(self, room_id, client_data:Connection):
        '''This method allows the user to switch between rooms.'''
        if not room_id in self.setting.server_rooms:
            self.protocol.send('Room %s not found.' % room_id, client_data.socket)
            return
        for room in self.rooms:
            room.disconnect(client_data)
            if room.name == room_id:
                room.connect(client_data)
                self.protocol.send(room.get_users(), client_data.socket)

    def __connect(self, client_data:Connection):
        '''This method either terminates the connection or passes the user to the server if the authorization was successful.'''
        if self._signin(client_data):
            client_data.thread = Thread(target=self.__handler, args=[client_data])
            client_data.thread.daemon = True
            client_data.thread.start()
            self.connections.append(client_data)
            self.__change_room("guest", client_data)
            print(str(client_data.nickname), "connected", len(self.connections))
        else:
            print('Connection denied.')
            client_data.socket.close()

    # Server startup method
    def run(self):
        '''This method handles connection attempts.'''
        self.state = STATE_WORKING
        while self.state == STATE_WORKING:
            c, a = self.accept()
            client_data = Connection(c, a)
            autorisation_thread = Thread(target=self.__connect, args=[client_data])
            autorisation_thread.start()

            
    
    def stop(self):
        self.state = STATE_STOPPING
        for thread in self.threads:
            thread.do_run = False
            thread.join()