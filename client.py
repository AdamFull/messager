import socket as s
from threading import Thread
import json
import sys
import struct

class client:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)               #Создаём сетевой сокет
    def __init__(self, nickname, address, port = 9191):
        self.sock.connect((address, port))
        self.nickname = nickname

        thread = Thread(target=self.send)
        thread.daemon = True
        thread.start()
        while True:
            data = self.recv()
            if not data:
                break
            raw_data = json.loads(data)
            print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))
    
    def send(self): #Отправка сообщений
        while True:
            msg_data = {"nickname" : self.nickname, "msg" : input(">>")}
            raw_data = json.dumps(msg_data, ensure_ascii=False).encode('utf-8')
            msg = struct.pack('>I', len(raw_data)) + raw_data
            self.sock.sendall(msg)
    
    def recv(self): #Метод для принятия сообщений
        raw_msglen = self.recvall(4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.recvall(msglen)

    def recvall(self, n): #Вспомогательный метод для принятия сообщений, читает из сокета
        data = b''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

if len(sys.argv) > 1:
    clt = client(sys.argv[1] ,'localhost', 9191)