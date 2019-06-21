#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
import threading
import json

STATE_READY = 0
STATE_WORKING = 1
STATE_STOPPING = 3

class ServerSettings:
    def __init__(self):
        self.server_ip = '0.0.0.0'
        self.server_port = 9191
        self.maximum_users = 100
        self.server_rooms = ['guest' ,'proggers', 'russian', 'pole']
class Server:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)  # Создаём сетевой сокет
    sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #Это позволяет испольдовать сокет даже если он не был корректно закрыт
    connections = list()  # Лист для хранения всех подключений
    threads = list()

    def __init__(self):
        self.setting = ServerSettings()
        self.sock.bind((self.setting.server_ip, self.setting.server_port))  # Задаём параметры сокета
        self.sock.listen(self.setting.maximum_users)  # Слушаем сокет
        self.state = STATE_READY

    def handler(self, client_index):
        thread = threading.current_thread()
        while self.state == STATE_WORKING and getattr(thread, "do_run", True):
            try:
                data = self.connections[client_index][0].recv(1024)  # Читаем клиент
            except s.error as e:
                if e.errno == s.errno.ECONNRESET:
                    print(str(self.connections[client_index][1][0]) + ':' + str(self.connections[client_index][1][1]), "disconnected", len(self.connections))
                    self.threads.remove(thread)
                    self.connections[client_index][0].close()
                    self.connections.pop(client_index)
                    break
                else:
                    print(e)
                    raise
            
            for connection in self.connections:
                if connection[2] == self.connections[client_index][2] and connection != self.connections[client_index]:
                    connection[0].send(data)  # Отправляем всем клиентам в этой же комнате
    
    def change_room(self, self_id, room_id):
        pass

    def run(self):
        self.state = STATE_WORKING
        while self.state == STATE_WORKING:
            c, a = self.sock.accept()
            room = self.setting.server_rooms[0]
            client_data = [c, a, room]
            self.connections.append(client_data)
            self_index = self.connections.index(client_data)
            self.threads.append(threading.Thread(target=self.handler, args=[self_index]))  # Отдельный поток для хандлера
            self.threads[len(self.threads) - 1].daemon = True
            self.threads[len(self.threads) - 1].start()
            print(str(a[0]) + ':' + str(a[1]), "connected", len(self.connections))
    
    def stop(self):
        for thread in self.threads:
            thread.do_run = False
            thread.join()
        print("Threads closed.")


if __name__ == "__main__":
    srv = Server()
    srv.run()
