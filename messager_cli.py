#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
from threading import Thread
import server
import client

class Temp:
    def __init__(self, sock, client):
        self.sock = sock
        self.client = client
        self.version = 'alpha'
    
    def parse_command(self, string):
        args = string.split(" ")
        for a in args:
            if a == "p":
                print("New password: %s" % args[1])
                self.client.set_password(args[1])
                break
            elif a == "e":
                self.client.close()
                exit()
            elif a == "v":
                print(self.version)
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', action='store', dest='mode', default=False, help='Run server or client')
    parser.add_argument('-u', action="store", dest='user_name', help='User name')
    parser.add_argument('-pass', action="store", dest='password', help='User password')
    parser.add_argument('-a', action="store", dest='server_ip', help='Server IP address')
    parser.add_argument('-p', action="store", dest='server_port', type=int, help='Server TCP port')

    parsed = parser.parse_args()

    if parsed.mode == 'server':
        print("Start server")
        srv = server.Server()
        server_thread = Thread(target=srv.run)
        server_thread.start()
        while True:
            if input('>>') == 'stop':
                srv.stop()

    elif parsed.mode == 'client':
        cli_set = client.ClientSetting()
        if parsed.user_name:
            user_name = parsed.user_name
        if parsed.password:
            password = parsed.password
        if parsed.server_ip:
            server_ip = parsed.server_ip
        if parsed.server_port:
            port = parsed.server_port
        cli_set.update(user_name, password, server_ip, port)

        net_client = client.Client()
        tmp = Temp(net_client.sock, net_client)
        while True:
            input_msg = input('>>')
            if(input_msg[0] == "/"):
                tmp.parse_command(input_msg.split("/")[1])
            else:
                net_client.send(input_msg)

    #wait for server stop
    server_thread.join()
