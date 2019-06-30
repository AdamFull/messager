from client import Client, ClientSetting
from autologging import logged, TRACE, traced
from logging import basicConfig
from threading import Thread
from datetime import datetime
from argparse import ArgumentParser
from os import path, makedirs

class Temp:
    def __init__(self, sock, client):
        self.sock = sock
        self.client = client
        self.version = 'alpha'
        self.client_log = 'Log/'

        if not path.exists(self.client_log):
            makedirs(self.client_log)
    
    def parse_command(self, string):
        args = string.split(" ")
        command = args[0]
        if command == "p":
            if len(args) > 1:
                print("New password: %s" % args[1])
                self.client.set_password(args[1])
            else:
                print('Not enought arguments.')
        elif command == "e":
            self.client.close()
            exit()
        elif command == "v":
            print(self.version)
        elif command == "d":
            self.client.disconnect()
        elif command == "c":
            connection_args = args[1].split(":")
            self.client.connect(connection_args[0], int(connection_args[1]))
        elif command == "server":
            self.client.server_command(string)

if __name__ == "__main__":
    basicConfig(filename='%s/log_%s.log' % ('Log', datetime.now().strftime("%Y-%m-%d-%H-%M-%S")),
                            level=TRACE,
                            format="%(levelname)s:%(filename)s,%(lineno)d:%(name)s.%(funcName)s:%(message)s")
    
    parser = ArgumentParser()
    parser.add_argument('-u', action="store", dest='user_name', help='User name')
    parser.add_argument('-n', action="store", dest='nick_name', help='Nickname')
    parser.add_argument('-pass', action="store", dest='password', help='Password')
    parser.add_argument('-a', action="store", dest='server_ip', help='Server IP address')
    parser.add_argument('-p', action="store", dest='server_port', type=int, help='Server TCP port')

    parsed = parser.parse_args()

    cli_set = ClientSetting([parsed.user_name, parsed.nick_name, parsed.password,
    parsed.server_ip, parsed.server_port])
    
    cli_set.save()

    net_client = Client()

    temp = Temp(net_client.sock, net_client)
    client_thread = Thread(target=net_client.run)
    client_thread.start()
    while True:
        input_msg = input('>>')
        if net_client.isLogined:
            if not input_msg is '':
                if(input_msg[0] == "/"):
                    temp.parse_command(input_msg.split("/")[1])
                else:
                    net_client.send(input_msg)
        else:
            net_client.send_verification_key(input_msg)