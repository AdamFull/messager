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
    threads = list()

    def __init__(self):
        self.sock.bind(('0.0.0.0', 9191))  # Задаём параметры сокета
        self.sock.listen(1)  # Слушаем сокет
        self.state = STATE_READY

    def handler(self, c, a):
        while self.state == STATE_WORKING:
            try:
                data = c.recv(1024)  # Читаем клиент
            except s.error as e:
                if e.errno == s.errno.ECONNRESET:
                    print(str(a[0]) + ':' + str(a[1]), "disconnected", len(self.connections))
                    self.connections.remove(c)
                    c.close()
                    break
                else:
                    print(e)
                    raise
            
            for connection in self.connections:
                connection.send(data)  # Отправляем всем клиентам

    def run(self):
        self.state = STATE_WORKING
        index = 0
        while self.state == STATE_WORKING:
            c, a = self.sock.accept()
            self.threads.append(Thread(target=self.handler, args=(c, a)))  # Отдельный поток для хандлера
            self.threads[len(self.threads) - 1].daemon = True
            self.threads[len(self.threads) - 1].start()
            self.connections.append(c)  # Добавляем подключения, если они были
            print(str(a[0]) + ':' + str(a[1]), "connected", len(self.connections))
            index += 1
    
    def stop(self):
        for thread in self.threads:
            thread.join()
        print("Threads closed.")


if __name__ == "__main__":
    srv = Server()
    srv.run()
