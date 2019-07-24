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
        self.socket: socket.socket = connection
        self.status = ''
        self.connection_status = False
        self.ip: str = args[0]
        self.port: int = args[1]
        self.nickname = ''
        self.rsa_public = ''
        self.thread: Thread = None

class Registration:
    def __init__(self, connection:Connection, setting:ServerSettings):
        self.server_database = ServerDatabase()
        self.setting = setting
        self.connection = connection
    
    def verificate(self, username):
        data = self.setting.protocol.response(self.connection.socket).decode()
        if data:
            # We are waiting for the code word from the user
            self.setting.protocol.request({"verification": ""}, self.connection.socket)
        else:
            return False
            
        return True if self.server_database.verificate_user(username, data) else False

    # User registration on the server
    def signup(self, data):
        username = data[0]
        public_key = data[1]
        if self.setting.enable_password:
            self.server_database.add_user_with_verification(username, public_key)
            if self.verificate(username):
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
            data = self.setting.protocol.response(self.connection.socket)
            if "wanna_connect" in data.keys():
                self.setting.protocol.request({"userdata": ""}, self.connection.socket)
                data = self.setting.protocol.response(self.connection.socket)
                username, public_key = data["nickname"], data["public_key"]
        else:
            username, public_key = data[0], data[1]
        
        self.connection.nickname = username
        self.connection.rsa_public = public_key

        if self.server_database.is_user_already_exist(username):
            if self.server_database.is_user_verificated(username):
                if self.server_database.is_keys_match(username, public_key):
                    key = self.setting.encrypt_key(self.setting.protocol.aes_key, public_key)
                    self.setting.protocol.request({"success": key.decode()}, self.connection.socket)
                    return True
                else:
                    self.setting.protocol.request({"key_error": ""}, self.connection.socket)
                    return False
            else:
                if self.verificate(username):
                    self.signin([username, str(public_key)])
                    return True
                else:
                    self.setting.protocol.request({"verification_error": ""}, self.connection.socket)
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
    connections = dict() # List for contains connections

    def __init__(self):
        super(Server, self).__init__(socket.AF_INET, socket.SOCK_STREAM) # Creating network socket for server
        self.setting = ServerSettings()
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # This allows you to use a socket even if it was not properly closed.
        self.bind((self.setting.server_ip, self.setting.server_port))  # Configure server socket
        self.listen(self.setting.maximum_users)  # Listen socket N connections
        self.state = STATE_READY

    def handler(self, client_connection:Connection):
        while self.state == STATE_WORKING and getattr(client_connection.thread, "do_run", True):
            try:
                data = self.setting.protocol.recv(client_connection.socket)  # Reading client
                if data:
                    if(self.parse_client_command(data, client_connection)):
                        continue
                    self.sendToChat(data)
                else:
                    raise socket.error
            except socket.error:
                client_connection.socket.close() # close client socket
                self.connections.pop(client_connection.nickname) # remove client from server
                break
    
    def sendToChat(self, data):
        if "msg" in data.keys():
            chat_usrs = self.setting.database.get_users_in_chat(data["chat"])
            offline = []
            for usr in chat_usrs:
                try:
                    self.setting.protocol.send(data, self.connections[usr].socket)
                except KeyError:
                    offline.append(usr) if not usr == "server" else None


    def parse_client_command(self, data, client_data:Connection):
        '''This method is responsible for processing commands from the client.'''
        keys = data.keys()
        if "cmd" in keys:
            if "value" in keys:
                if data["cmd"] == "chchat":
                    self.change_chat(data["value"], client_data)
                    return True
                if data["cmd"] == "fchat":
                    if not data["value"]:
                        self.setting.protocol.send({"chats": self.setting.database.get_user_chats(client_data.nickname)}, client_data.socket)
                    else:
                        self.setting.protocol.send({"chats": self.setting.database.get_chats_like(data["value"])}, client_data.socket)
                    return True
            if data["cmd"] == "chats":
                self.setting.protocol.send({"chats": self.setting.database.get_user_chats(client_data.nickname)}, client_data.socket)
                return True
        return False

    def change_chat(self, room_id, client_data:Connection):
        '''This method allows the user to switch between rooms.'''
        if not room_id in self.setting.server_rooms:
            self.setting.protocol.send({"info": "Chat %s not found."} % room_id, client_data.socket)
            return
        for room in self.rooms:
            room.disconnect(client_data)
            if room.name == room_id:
                room.connect(client_data)
                self.setting.protocol.send({"users": self.setting.database.get_users_in_chat(room_id)}, client_data.socket)

    def connect(self, client_data:Connection):
        '''This method either terminates the connection or passes the user to the server if the authorization was successful.'''
        if Registration(client_data, self.setting).signin():
            client_data.thread = Thread(target=self.handler, args=[client_data])
            client_data.thread.daemon = True
            client_data.thread.start()
            self.connections.update({client_data.nickname: client_data})
            self.setting.database.join_to_chat("server_main", client_data.nickname)
        else:
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