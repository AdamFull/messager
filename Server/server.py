#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
from threading import Thread
from protocol import Protocol
from autologging import logged, traced
from server_database import ServerDatabase, ServerSettings, RSACrypt
from json import loads, dumps

STATE_READY = 0
STATE_WORKING = 1
STATE_STOPPING = 3

class Room(object):
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

class Connection(socket.socket):
    def __init__(self, connection:socket.socket, args):
        super(Connection, self).__init__()
        self.socket: s.socket = connection
        self.ip: str = args[0]
        self.port: int = args[1]
        self.nickname = ''
        self.rsa_public = ''
        self.room = ''
        self.thread: Thread = None

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
        self.aes_key = self.setting.aes_key()

    def __handler(self, client_connection:Connection):
        while self.state == STATE_WORKING and getattr(client_connection.thread, "do_run", True):
            try:
                data = self.protocol.recv(client_connection.socket)  # Читаем клиент
                self.__parse_client_command(data, client_connection)
            except socket.error as e:
                if e.errno == socket.errno.ECONNRESET:
                    print(str(client_connection.ip) + ':' + str(client_connection.port), "disconnected", len(self.connections))
                    client_connection.socket.close()
                    self.connections.pop(self.connections.index(client_connection))
                    break
                else:
                    print(e)
                    raise
            for connection in self.connections:
                if connection.room == client_connection.room and connection != client_connection:
                    # RSACrypt(connection.rsa_public).encrypt(data, connection.rsa_public)
                    self.protocol.send(data, connection.socket)  # Отправляем всем клиентам в этой же комнате
    
    def __parse_server_command(self, data):
        if not data == None:
            args = data.split(' ')
    
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
            return
        if not data == None and "server" in string_data:
            args = data.decode('utf-8').split(' ')
            if len(args) > 1:
                command = args[1]
                if command == 'rooms':
                    self.protocol.send('ROOMS,'+','.join(self.setting.server_rooms), client_data.socket)
                    return
                if command == 'clients':
                    return
            if len(args) > 2:
                command = args[1]
                if command == 'chroom':
                    self.__change_room(args[2], client_data)
            else:
                self.protocol.send("Not Enought arguments.",client_data.socket)

    def __change_room(self, room_id, client_data:Connection):
        '''This method allows the user to switch between rooms.'''
        last: Connection = self.connections.pop(self.connections.index(client_data))
        if room_id in self.setting.server_rooms:
            last.room = room_id
            self.connections.append(last)
            for connection in self.connections:
                if connection.room == room_id and connection != client_data:
                    self.protocol.send("%s connected to room %s." % (last.nickname, room_id), connection.socket)
        else:
            self.protocol.send('Room %s not found.' % room_id, last.socket)

    def __connect(self, client_data:Connection):
        '''This method either terminates the connection or passes the user to the server if the authorization was successful.'''
        if self._signin(client_data):
            client_data.thread = Thread(target=self.__handler, args=[client_data])
            client_data.thread.daemon = True
            client_data.thread.start()
            self.connections.append(client_data)
            self.__change_room("guest", client_data)
            print(str(client_data.ip) + ':' + str(client_data.port), "connected", len(self.connections))
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