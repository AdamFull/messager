#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
from threading import Thread
from autologging import logged, traced
from server_database import ServerDatabase, ServerSettings, RSACrypt, sha_hd
from json import dumps, loads

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
        self.user_uid = ''
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
        user_uid = data[1]
        public_key = data[2]
        if self.setting.enable_password:
            self.server_database.add_user_with_verification(username, user_uid, public_key)
            if self.verificate(user_uid):
                return True
            else:
                return False
        else:
            self.server_database.add_user_without_verification(username, user_uid, public_key)
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
                username, user_uid, public_key = data["nickname"], sha_hd(data["public_key"]), data["public_key"]
        else:
            username, user_uid, public_key = data[0], data[1], data[2]
        
        self.connection.nickname = username
        self.connection.user_uid = user_uid
        self.connection.rsa_public = public_key

        if self.server_database.is_user_already_exist(user_uid):
            if self.server_database.is_user_verificated(user_uid):
                if self.server_database.is_keys_match(user_uid, public_key):
                    key = self.setting.encrypt_key(self.setting.protocol.aes_key, public_key)
                    self.setting.protocol.request({"success": key.decode()}, self.connection.socket)
                    return True
                else:
                    self.setting.protocol.request({"key_error": ""}, self.connection.socket)
                    return False
            else:
                if self.verificate(user_uid):
                    self.signin([username, user_uid, str(public_key)])
                    return True
                else:
                    self.setting.protocol.request({"verification_error": ""}, self.connection.socket)
                    return False
        else:
            if self.signup([username, user_uid, str(public_key)]):
                self.signin([username, user_uid, str(public_key)])
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
                    self.send(data)
                else:
                    raise socket.error
            except socket.error:
                client_connection.socket.close() # close client socket
                self.connections.pop(client_connection.user_uid) # remove client from server
                break
    
    def send(self, data):
        if "msg" in data.keys():
            chat_usrs = self.setting.database.get_users_in_chat(data["chat"])
            offline = []
            for usr in chat_usrs:
                try:
                    self.send_for(data, self.connections[usr].user_uid)
                except KeyError:
                    self.setting.database.add_to_queue(dumps(data), usr) if not usr == "server" else None
    
    def send_for(self, data, user):
        self.setting.protocol.send(data, self.connections[user].socket)


    def parse_client_command(self, data, client_data:Connection):
        '''This method is responsible for processing commands from the client.'''
        keys = data.keys()
        g_c_s = lambda x: self.setting.database.get_chat_settings(x)
        g_c_l = lambda x: self.setting.database.get_chats_like(x)
        g_u_c = lambda x: self.setting.database.get_user_chats(x)
        f_u_l = lambda x: self.setting.database.find_user(x)
        g_u_n = lambda x: self.setting.database.get_username(x)
        if "cmd" in keys:
            if "value" in keys:
                if data["cmd"] == "jchat":
                    self.setting.database.join_to_chat(data["value"], client_data.user_uid)
                    return True
                if data["cmd"] == "fchat":
                    if not data["value"]:
                        self.setting.protocol.send({"chats": {data: g_c_s(data) for data in g_u_c(client_data.user_uid)}}, client_data.socket)
                    else:
                        finded = g_c_l(data["value"])
                        self.setting.protocol.send({"chats": {data: g_c_s(data) for data in finded} if finded else None}, client_data.socket)
                    return True
                if data["cmd"] == "fuser":
                    if not data["value"]:
                        self.setting.protocol.send({"chats": {data: g_c_s(data) for data in g_u_c(client_data.user_uid)}}, client_data.socket)
                    else:
                        finded = f_u_l(data["value"])
                        self.setting.protocol.send({"users": {g_u_n(data): data for data in finded if data != client_data.user_uid} if finded else None}, client_data.socket)
                if data["cmd"] == "mchat":
                    if(self.setting.database.create_chat(data["value"], client_data.user_uid)):
                        self.setting.protocol.send({"chats": {data: g_c_s(data) for data in g_u_c(client_data.user_uid)}}, client_data.socket)
                        self.setting.protocol.send({"info": "Chat created!"}, client_data.socket)
                    else:
                        self.setting.protocol.send({"info": "Error!"}, client_data.socket)

            if data["cmd"] == "chats":
                self.setting.protocol.send({"chats": {data: g_c_s(data) for data in g_u_c(client_data.user_uid)}}, client_data.socket)
                return True
            if data["cmd"] == "disconnect":
                self.setting.protocol.send({"info": "Nu i vali otsuda koresh."}, client_data.socket)
                return True
            if data["cmd"] == "friends":
                g_f = lambda x: [self.setting.database.get_username(uid) for uid in self.setting.database.get_friends(x)]
                self.setting.protocol.send({"friends": g_f(client_data.user_uid)}, client_data.socket)
        return False
    
    def send_qeued(self, client_data: Connection):
        messages = self.setting.database.get_user_queue(client_data.user_uid)
        for message in messages:
            self.send_for(loads(message), client_data.user_uid)
        self.setting.database.remove_from_queue(client_data.user_uid)

    def connect(self, client_data:Connection):
        '''This method either terminates the connection or passes the user to the server if the authorization was successful.'''
        if Registration(client_data, self.setting).signin():
            client_data.thread = Thread(target=self.handler, args=[client_data])
            client_data.thread.daemon = True
            client_data.thread.start()
            self.connections.update({client_data.user_uid: client_data})
            self.setting.database.join_to_chat("server_main", client_data.user_uid)
            queue = self.setting.database.get_queue()
            if queue:
                if client_data.user_uid in queue:
                    self.send_qeued(client_data)
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