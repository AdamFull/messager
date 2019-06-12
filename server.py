#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
from threading import Thread
import json

STATE_READY = 0
STATE_WORKING = 1
STATE_STOPPING = 3

class Server:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)  # Создаём сетевой сокет
    sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #Это позволяет испольдовать сокет даже если он не был корректно закрыт
    connections = list()  # Лист для хранения всех подключений

    def __init__(self):
        self.sock.bind(('0.0.0.0', 9191))  # Задаём параметры сокета
        self.sock.listen(1)  # Слушаем сокет
        self.state = STATE_READY

    def handler(self, c, a):
        while self.state == STATE_WORKING:
            data = c.recv(1024)  # Читаем клиент
            for connection in self.connections:
                connection.send(data)  # Отправляем всем клиентам
            if not data:
                print(str(a[0]) + ':' + str(a[1]), "disconnected", len(self.connections))
                self.connections.remove(c)
                c.close()
                break
    
    def server_command(self, command):
        pass

    def run(self):
        self.state = STATE_WORKING
        while self.state == STATE_WORKING:
            c, a = self.sock.accept()
            thread = Thread(target=self.handler, args=(c, a))  # Отдельный поток для хандлера
            thread.daemon = True
            thread.start()
            self.connections.append(c)  # Добавляем подключения, если они были
            print(str(a[0]) + ':' + str(a[1]), "connected", len(self.connections))


if __name__ == "__main__":
    srv = Server()
    srv.run()
