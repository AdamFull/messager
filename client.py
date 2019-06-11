import socket as s
from threading import Thread

class client:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM) #Создаём сетевой сокет
    def __init__(self, address, port = 9191):
        self.sock.connect((address, port))
        thread = Thread(target=self.send)
        thread.daemon = True
        thread.start()
        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            print(data)
    
    def send(self):
        while True:
            self.sock.send(bytes(input(""), 'utf-8'))

clt = client('localhost', 9191)