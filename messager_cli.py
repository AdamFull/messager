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
        command = args[0]
        if command == "p":
            print("New password: %s" % args[1])
            self.client.set_password(args[1])
        elif command == "e":
            self.client.close()
            exit()
        elif command == "v":
            print(self.version)
        elif command == "d":
            self.client.disconnect()
        elif command == "c":
            if len(args) > 1:
                connection_args = args[1].split(":")
                self.client.connect(connection_args[0], int(connection_args[1]))
            else:
                self.client.connect()




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', action='store', dest='mode', default=False, help='Run server or client')
    parser.add_argument('-u', action="store", dest='user_name', help='User name')
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
            cli_set.nickname = parsed.user_name
        if parsed.server_ip:
            cli_set.server_ip = parsed.server_ip
        if parsed.server_port:
            cli_set.port = parsed.server_port

        net_client = client.Client(cli_set.nickname, cli_set.server_ip, cli_set.port)
        tmp = Temp(net_client.sock, net_client)
        while True:
            input_msg = input('>>')
            if(input_msg[0] == "/"):
                tmp.parse_command(input_msg.split("/")[1])
            else:
                net_client.send(input_msg)

    #wait for server stop
    server_thread.join()
