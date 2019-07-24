#!/usr/bin/python3
# -*- coding: utf-8 -*-

import __future__
import socket
import threading
from os import system
from json import dumps, loads
from autologging import logged, traced
from hashlib import sha256
from client_settings import ClientDatabase
from abc import ABC, abstractmethod
from typing import List
from time import gmtime, strftime, sleep

class STATEMENT:
        DISCONNECTED = 0
        CONNECTED = 1
        VERIFICATION = 2

class Subject(ABC):
    @abstractmethod
    def attach(self, observer) -> None:
        # Add an observer
        pass
    
    @abstractmethod
    def detach(self, observer) -> None:
        # Remove an observer
        pass
    
    @abstractmethod
    def notify(self) -> None:
        # Notify observer
        pass

class Observer(ABC):
    @abstractmethod
    def update(self, subject:Subject) -> None:
        pass

@traced
@logged
class Client(Subject):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _STATE: int = STATEMENT().DISCONNECTED # Current client state
    _CURRENT_MESSAGE: str = ''             # Current client message
    _observers: List = []                  # Observres list
    def __init__(self, receive_callback=None):
        self.setting = ClientDatabase()

        self.thread: threading.Thread = None

        #This callback sets by frontend to handle incoming messages
        self.rcv_output = receive_callback

        self.current_chat = None

        self.isConnected = False
        self.isLogined = False
    
    def attach(self, observer:Observer) -> None:
        self._observers.append(observer)
    
    def detach(self, observer:Observer) -> None:
        self._observers.remove(observer)
    
    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)
    
    def change_message(self, data):
        self._CURRENT_MESSAGE = data
        self.notify()

    def listen(self):
        current_thread = threading.current_thread()
        while getattr(current_thread, "do_run", True):
            try:
                data = self.setting.protocol.recv(self.sock)
                if data:
                    if self.rcv_output:
                        self.rcv_output(data)
                    
                    self.change_message(data)

            except socket.error:
                self._STATE = STATEMENT().DISCONNECTED
                self.change_message({"status": 'Current connection: none.'})
                self.close()
                break

    def login(self):
        self.setting.protocol.request({"wanna_connect": ""}, self.sock) # Sending connection request to server.
        while True:
            response = self.setting.protocol.response(self.sock)
            if response:
                response_keys = response.keys()
                if "success" in response_keys:
                    self.setting.protocol.aes_key = self.setting.protocol.RSA.decrypt(response["success"])
                    return True
                elif "verification" in response_keys:
                    self._STATE = STATEMENT().VERIFICATION
                elif "key_error" in response_keys:
                    self.change_message({"status": "Keys don't match"})
                    return False
                elif "userdata" in response_keys:
                    self.setting.protocol.request({"nickname": self.setting.nickname, "public_key": self.setting.protocol.RSA.export_public().decode()}, self.sock)
                else:
                    return False
            else:
                if self._STATE == STATEMENT().VERIFICATION:
                    self.change_message({"status": "Waiting varification key."})
                else:
                    self.change_message({"status": "Waiting server response."})
                continue
        return False
    
    def send_verification_key(self, key):
        key_hash = sha256(key.encode()).hexdigest()
        self.setting.protocol.sendws(key_hash, self.sock)

    def connect(self, ip, port, attempts = 5):
        if self._STATE == STATEMENT().CONNECTED:
            self.change_message({"status": "Allready connected to: %s:%s" % (self.setting.server_ip, self.setting.server_port)})
            return False
        self.change_message({"status": "Trying to connect: %s:%s" % (ip, port)})
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
        except Exception as e:
            if attempts > 0:
                attempt = attempts-1
                return self.connect(ip, port, attempt)
            else:
                self.change_message({"status": 'Connection failed.'})
                return False
        #self.setting.server_ip = ip
        #self.setting.server_port = port

        if self.login():
            self.isLogined = True
            self._STATE = STATEMENT().CONNECTED
            self.change_message({"status": "Current connection: %s:%s" % (ip, port)})
            self.thread = threading.Thread(target=self.listen)
            self.thread.daemon = True
            self.thread.do_run = True
            self.thread.start()
            return True
        else:
            return False
    
    def disconnect(self) -> None:
        self.change_message({"status": "Disconnecting from server."})
        self._STATE = STATEMENT().DISCONNECTED
        self.isLogined = False
        self.thread.do_run = False
        self.sock.close()
        self.thread.join()
    
    def run(self) -> None:
        self.connect(self.setting.server_ip, self.setting.server_port)
    
    def server_command(self, command) -> None:
        self.setting.protocol.send(command, self.sock)
    
    def change_chat(self, chat):
        self.current_chat = chat
        self.setting.join_to_chat(chat)
        self.server_command({"cmd": "jchat", "value": chat})
    
    def create_chat(self, chat):
        self.server_command({"cmd": "mchat", "value": chat})
        sleep(1)
        self.change_chat(chat)
    
    def find_request(self, data):
        self.server_command({"cmd": "fchat", "value": data})
    
    def send(self, input_msg): #Message sending method
        msg_data = {"nickname": self.setting.nickname, "msg": input_msg, "chat": self.current_chat, "time": strftime("%H:%M:%S", gmtime()), "date": strftime("%Y-%m-%d", gmtime())}
        self.setting.protocol.send(msg_data, self.sock)
    
    def close(self):
        self.sock.detach()