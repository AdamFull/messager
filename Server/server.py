#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
from threading import Thread
from autologging import logged, traced
from server_database import ServerDatabase, ServerSettings, RSACrypt

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
    def __init__(self, name, protocol):
        super(Room, self).__init__()
        self.name = name
        self.users = list()
        self.protocol = protocol
    
    def connect(self, connection:Connection) -> None:
        if not connection in self.users:
            self.users.append(connection)
            self.send({"info": "%s connected to chat." % connection.nickname}, connection)
    
    def disconnect(self, connection:Connection) -> None:
        if connection in self.users:
            self.send({"info": "%s left the chat." % connection.nickname}, connection)
            self.users.pop(self.users.index(connection))
    
    def get_users(self):
        return {"users": ''.join(user.nickname for user in self.users)}
    
    def send(self, data, client:Connection):
        for connection in self.users:
            if connection != client and client in self.users:
                self.protocol.send(data, connection.socket, True)

class Registration:
    def __init__(self, connection:Connection, setting:ServerSettings):
        self.server_database = ServerDatabase()
        self.setting = setting
        self.connection = connection
    
    def verificate(self, username):
        data = self.setting.protocol.recv(self.connection.socket).decode('utf-8')
        if data:
            # We are waiting for the code word from the user
            self.setting.protocol.send({"verification": ""}, self.connection.socket)
        else:
            print('Client lost connection.')
            return False
            
        return True if self.server_database.verificate_user(username, data) else False

    # User registration on the server
    def signup(self, data):
        username = data[0]
        public_key = data[1]
        if self.setting.enable_password:
            self.server_database.add_user_with_verification(username, public_key)
            if self.verificate(username, self.connection):
                return True
            else:
                return False
        else:
            self.server_database.add_user_without_verification(username, public_key)
            return True

    # User authorization on the server
    def signin(self, data=None):
        '''This method is responsible for authorizing the client if it was registered,\n 
        and for registering if the client is not found.'''
        if not data:
            if "wanna_connect" in self.setting.protocol.recv(self.connection.socket).keys():
                self.setting.protocol.send({"userdata": ""}, self.connection.socket)
                data = self.setting.protocol.recv(self.connection.socket)
                username, public_key = data["nickname"], data["public_key"]
        else:
            username, public_key = data[0], data[1]
        
        self.connection.nickname = username
        self.connection.rsa_public = public_key

        if self.server_database.is_user_already_exist(username):
            if self.server_database.is_user_verificated(username):
                if self.server_database.is_keys_match(username, public_key):
                    key = self.setting.encrypt_key(self.setting.protocol.aes_key, public_key)
                    self.setting.protocol.send({"success": key.decode()}, self.connection.socket)
                    return True
                else:
                    self.setting.protocol.send({"key_error": ""}, self.connection.socket)
                    return False
            else:
                if self.verificate(username):
                    self.signin([username, str(public_key)])
                    return True
                else:
                    self.setting.protocol.send({"verification_error": ""}, self.connection.socket)
                    return False
        else:
            if self.signup([username, str(public_key)]):
                self.signin([username, str(public_key)])
                return True
            else:
                # Unknown error.
                return False

@traced
@logged
class Server(socket.socket):
    connections = list() # List for contains connections

    def __init__(self):
        super(Server, self).__init__(socket.AF_INET, socket.SOCK_STREAM) # Creating network socket for server
        self.setting = ServerSettings()
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # This allows you to use a socket even if it was not properly closed.
        self.bind((self.setting.server_ip, self.setting.server_port))  # Configure server socket
        self.listen(self.setting.maximum_users)  # Listen socket N connections
        self.state = STATE_READY
        self.rooms = [Room(name, self.setting.protocol) for name in self.setting.server_rooms]

    def handler(self, client_connection:Connection):
        while self.state == STATE_WORKING and getattr(client_connection.thread, "do_run", True):
            data = self.setting.protocol.recv(client_connection.socket, True)  # Reading client
            if data:
                if(self.parse_client_command(data, client_connection)):
                    continue
                for room in self.rooms:
                    room.send(data, client_connection)
            else:
                print(str(client_connection.nickname), "disconnected", len(self.connections))
                for room in self.rooms:
                    room.disconnect(client_connection) # disconnect client from rooms
                client_connection.socket.close() # close client socket
                self.connections.pop(self.connections.index(client_connection)) # remove client from server
                break

    def parse_client_command(self, data, client_data:Connection):
        '''This method is responsible for processing commands from the client.'''
        keys = data.keys()
        if "cmd" in keys:
            if "value" in keys:
                if data["cmd"] == "chroom":
                    self.change_room(data["value"], client_data)
                    return True
            if data["cmd"] == "rooms":
                self.setting.protocol.send({"rooms": self.setting.server_rooms}, client_data.socket, True)
                return True
        return False

    def change_room(self, room_id, client_data:Connection):
        '''This method allows the user to switch between rooms.'''
        if not room_id in self.setting.server_rooms:
            self.setting.protocol.send({"info": "Room %s not found."} % room_id, client_data.socket, True)
            return
        for room in self.rooms:
            room.disconnect(client_data)
            if room.name == room_id:
                room.connect(client_data)
                self.setting.protocol.send({"users": room.get_users()}, client_data.socket, True)

    def connect(self, client_data:Connection):
        '''This method either terminates the connection or passes the user to the server if the authorization was successful.'''
        if Registration(client_data, self.setting).signin():
            client_data.thread = Thread(target=self.handler, args=[client_data])
            client_data.thread.daemon = True
            client_data.thread.start()
            self.connections.append(client_data)
            self.change_room("guest", client_data)
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
            autorisation_thread = Thread(target=self.connect, args=[client_data])
            autorisation_thread.start()

            
    
    def stop(self):
        self.state = STATE_STOPPING
        for thread in self.threads:
            thread.do_run = False
            thread.join()