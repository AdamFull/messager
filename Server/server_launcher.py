#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

from server import Server
from os import makedirs, getpid
from os.path import dirname, exists, abspath, isfile
from autologging import logged, TRACE, traced
from logging import basicConfig
from threading import Thread
from time import gmtime, strftime, sleep
from psutil import Process, virtual_memory
import sys

__version__ = [0, 4, 1, "alpha", "release"]

if __name__ == "__main__":
    print("Starting server.")

    show_stat = True
    if len(sys.argv) > 1 and sys.argv[1] == "-d":
        show_stat = False

    log_path = dirname(abspath(__file__)) + '/Log/'

    if not exists(log_path):
            makedirs(log_path)

    basicConfig(filename='%s/log_%s.log' % ('Log', strftime("%Y-%m-%d-%H-%M-%S", gmtime())),
                            level=TRACE,
                            format="%(levelname)s:%(filename)s,%(lineno)d:%(name)s.%(funcName)s:%(message)s")
                            #, stream=sys.stderr
    srv = Server()
    server_thread = Thread(target=srv.run)
    server_thread.start()

    print("VERSION: ", __version__)

    self_usage = Process(getpid())
    while True:
        sleep(1)
        if show_stat:
            u_cpu = int(self_usage.cpu_percent())
            u_memory = int(self_usage.memory_info()[0]/2.**20)
            t_memory = int(virtual_memory()[0]/2.**20)
            u_disk = int(self_usage.io_counters()[0]/self_usage.io_counters()[1])
            o_slots = len(srv.connections.keys())
            t_slots = srv.setting.maximum_users
            sys.stdout.write("\rSERVER MONITOR [CPU: %s%% | RAM: %s/%s Mb | DISK: %s%% | SLOTS: %s/%s]" % (u_cpu, u_memory, t_memory, u_disk, o_slots, t_slots))
            sys.stdout.flush()