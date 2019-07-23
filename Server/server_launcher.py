from server import Server
from os import makedirs, getpid
from os.path import dirname, exists, abspath, isfile
from autologging import logged, TRACE, traced
from logging import basicConfig
from threading import Thread
from time import gmtime, strftime, sleep
from psutil import Process, virtual_memory
import sys

if __name__ == "__main__":
    print("Starting server.")

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

    self_usage = Process(getpid())
    while True:
        sleep(1)
        u_cpu = self_usage.cpu_percent()
        u_memory = int(self_usage.memory_info()[0]/2.**20)
        t_memory = int(virtual_memory()[0]/2.**20)
        o_slots = 0
        t_slots = 100
        sys.stdout.write("\rSERVER MONITOR [CPU: %s%% | RAM: %s/%s Mb | SLOTS: %s/%s]" % (u_cpu, u_memory, t_memory, o_slots, t_slots))
        sys.stdout.flush()