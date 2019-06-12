#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
from threading import Thread
import server
import client


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
            srv.server_command(input('>>'))

    elif parsed.mode == 'client':
        cli_set = client.ClientSetting()
        if parsed.user_name:
            cli_set.nickname = parsed.user_name
        if parsed.server_ip:
            cli_set.server_ip = parsed.server_ip
        if parsed.server_port:
            cli_set.port = parsed.server_port

        net_client = client.Client(cli_set.nickname, cli_set.server_ip, cli_set.port)
        while True:
            net_client.send(input('>>'))

    #wait for server stop
    server_thread.join()
