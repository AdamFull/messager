import socket as s
from threading import Thread
import json

class server:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM) #Создаём сетевой сокет
    connections = list()                      #Лист для хранения всех подключений
    def __init__(self):
        self.sock.bind(('0.0.0.0', 9191))     #Задаём параметры сокета
        self.sock.listen(1)                   #Слушаем сокет

    def handler(self, c, a):
        while True:
            data = c.recv(1024)               #Читаем клиент
            for connection in self.connections:
                connection.send(data)         #Отправляем всем клиентам
            if not data:
                print(str(a[0]) + ':' + str(a[1]), "disconnected")
                self.connections.remove(c)
                c.close()
                break

    def run(self):
        while True:
            c, a = self.sock.accept()
            thread = Thread(target=self.handler, args=(c, a))   #Отдельный поток для хандлера
            thread.daemon = True
            thread.start()
            self.connections.append(c)                          #Добавляем подключения, если они были
            print(str(a[0]) + ':' + str(a[1]), "connected")

srv = server()
srv.run()