#!/usr/bin/python3
# -*- coding: utf-8 -*-

import __future__
import socket as s
import threading
from os import system
from json import dumps, loads
from protocol import Protocol
from autologging import logged, traced
from hashlib import sha256
from encryption import AESCrypt, RSACrypt
from client_settings import ClientSetting
from abc import ABC, abstractmethod
from typing import List

class STATEMENT:
        DISCONNECTED = 0
        CONNECTED = 1
        VERIFICATION = 2

class INFOTYPE:
    MESSAGE = "msg"
    STATUSBAR = "stat"
    SERVER = "srv"
    ROOMS = "rms"
    NONE = ""

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
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)
    _STATE: int = STATEMENT().DISCONNECTED # Current client state
    _INFOTYPE: INFOTYPE = INFOTYPE().NONE
    _CURRENT_MESSAGE: str = ''             # Current client message
    _observers: List = []                  # Observres list
    def __init__(self, receive_callback=None):
        self.setting = ClientSetting()

        self.thread: threading.Thread = None

        #This callback sets by frontend to handle incoming messages
        self.rcv_output = receive_callback

        self.isConnected = False
        self.isLogined = False
    
    def attach(self, observer:Observer) -> None:
        self._observers.append(observer)
    
    def detach(self, observer:Observer) -> None:
        self._observers.remove(observer)
    
    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)
    
    def change_message(self, msg, itype):
        self._INFOTYPE = itype
        self._CURRENT_MESSAGE = msg
        print(self._CURRENT_MESSAGE, self._INFOTYPE, self._STATE)
        self.notify()

    def iscrypted(self, data):
        try:
            data.decode('utf-8')
            return False
        except Exception:
            return True

    def listen(self):
        current_thread = threading.current_thread()
        while getattr(current_thread, "do_run", True):
            try:
                data = self.protocol.recv(self.sock)
            except Exception:
                self._STATE = STATEMENT().DISCONNECTED
                self.change_message('Current connection: none.', INFOTYPE().STATUSBAR)
                self.close()
                break

            if self.iscrypted(data):
                raw_data = loads(self.crypto.decrypt(data))
                if self.rcv_output:
                    self.rcv_output(raw_data)
                else:
                   self.change_message("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]), INFOTYPE().MESSAGE)
            else:
                tmp = data.decode('utf-8').split(',')
                if tmp[0] == "ROOMS":
                    self.change_message(','.join(tmp[1:]), INFOTYPE().ROOMS)
                else:
                    self.change_message(data.decode('utf-8'), INFOTYPE().SERVER)

    def login(self):
        self.protocol.send("wanna_connect", self.sock) # Sending connection request to server.
        while True:
            response = self.protocol.recv(self.sock)
            if response:
                response = response.decode('utf-8')
                if response == "success":
                    login_result = self.protocol.recv(self.sock)
                    self.setting.aes_session_key = self.setting.RSA.decrypt(login_result.decode('utf-8'))
                    self.crypto = AESCrypt(self.setting.aes_session_key)
                    return True
                elif response == "verification":
                    self._STATE = STATEMENT().VERIFICATION
                elif response == "key_error":
                    self.change_message("Keys don't match", INFOTYPE().STATUSBAR)
                    return False
                elif response == "userdata":
                    self.protocol.send(','.join([self.setting.username, self.setting.public_key.decode('utf-8')]), self.sock)
                elif response == "server_puplic_key":
                    self.setting.server_public_key = self.protocol.recv(self.sock).decode('utf-8') # Waiting server public rsa key.
                else:
                    return False
            else:
                if self._STATE == STATEMENT().VERIFICATION:
                    self.change_message("Waiting varification key.", INFOTYPE().STATUSBAR)
                else:
                    self.change_message("Waiting server response.", INFOTYPE().STATUSBAR)
                continue
        return False
        
        
    
    def send_verification_key(self, key):
        key_hash = sha256(key.encode('utf-8')).hexdigest()
        self.protocol.send(key_hash, self.sock)

    def connect(self, ip, port, attempts = 5):
        if self._STATE == STATEMENT().CONNECTED:
            self.change_message("Allready connected to: %s:%s" % (self.setting.server_ip, self.setting.port), INFOTYPE().STATUSBAR)
            return False
        self.change_message("Trying to connect: %s:%s" % (ip, port), INFOTYPE().STATUSBAR)
        try:
            self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.sock.connect((ip, port))
        except Exception as e:
            if attempts > 0:
                attempt = attempts-1
                return self.connect(ip, port, attempt)
            else:
                self.change_message('Connection failed.', INFOTYPE().STATUSBAR)
                return False
        self.setting.server_ip = ip
        self.setting.port = port

        self.protocol = Protocol()

        if self.login():
            self.isLogined = True
            self._STATE = STATEMENT().CONNECTED
            self.change_message("Current connection: %s:%s" % (ip, port), INFOTYPE().STATUSBAR)
            self.thread = threading.Thread(target=self.listen)
            self.thread.daemon = True
            self.thread.do_run = True
            self.thread.start()
            return True
        else:
            return False
    
    def disconnect(self):
        self.change_message("Disconnecting from server.", INFOTYPE().STATUSBAR)
        self._STATE = STATEMENT().DISCONNECTED
        self.isLogined = False
        self.thread.do_run = False
        self.sock.close()
        self.threadjoin()
    
    def run(self):
        self.setting.load_key()
        self.connect(self.setting.server_ip, self.setting.port)
    
    def server_command(self, command):
        self.protocol.send(command, self.sock)
    
    def send(self, input_msg): #Message sending method
        msg_data = {"nickname": self.setting.nickname, "msg": input_msg}
        raw_data = self.crypto.encrypt(dumps(msg_data, ensure_ascii=False).encode('utf-8'))
        self.protocol.send(raw_data, self.sock)
    
    def set_password(self, new_password):
        self.setting.password = new_password
        self.setting.save()
    
    def close(self):
        self.sock.detach()