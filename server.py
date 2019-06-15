#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
import json, random

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

        self.public_g = random.randint(1, 100)
        self.public_p = random.randint(100, 1000)

    def handler(self, c, a):
        thread = threading.current_thread()
        while self.state == STATE_WORKING and getattr(thread, "do_run", True):
            try:
                data = c.recv(1024)  # Читаем клиент
            except s.error as e:
                if e.errno == s.errno.ECONNRESET:
                    print(str(a[0]) + ':' + str(a[1]), "disconnected", len(self.connections), "in thread: ", thread.getName())
                    self.connections.remove(c)
                    self.threads.remove(thread)
                    c.close()
                    thread.do_run = False
                    break
                else:
                    print(e)
                    raise
            
            for connection in self.connections:
                connection.send(data)  # Отправляем всем клиентам

    def run(self):
        self.state = STATE_WORKING
        while self.state == STATE_WORKING:
            c, a = self.sock.accept()
            self.threads.append(threading.Thread(target=self.handler, args=(c, a)))  # Отдельный поток для хандлера
            self.threads[len(self.threads) - 1].daemon = True
            self.threads[len(self.threads) - 1].start()
            self.connections.append(c)  # Добавляем подключения, если они были
            print(str(a[0]) + ':' + str(a[1]), "connected", len(self.connections), "in thread: ", self.threads[len(self.threads) - 1].getName())

    def stop(self):
        for thread in self.threads:
            thread.do_run = False
            thread.join()
        print("Threads closed.")


if __name__ == "__main__":
    srv = Server()
    srv.run()
