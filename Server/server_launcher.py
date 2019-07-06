from server import Server
from os import makedirs
from os.path import dirname, exists, abspath, isfile
from autologging import logged, TRACE, traced
from logging import basicConfig
from threading import Thread
from datetime import datetime


if __name__ == "__main__":
    print("Starting server.")

    log_path = dirname(abspath(__file__)) + '/Log/'

    if not exists(log_path):
            makedirs(log_path)

    basicConfig(filename='%s/log_%s.log' % ('Log', datetime.now().strftime("%Y-%m-%d-%H-%M-%S")),
                            level=TRACE,
                            format="%(levelname)s:%(filename)s,%(lineno)d:%(name)s.%(funcName)s:%(message)s")
                            #, stream=sys.stderr
    srv = Server()
    server_thread = Thread(target=srv.run)
    server_thread.start()
    while True:
        command = input(">>")