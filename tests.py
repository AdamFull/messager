#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
import encryption
def crypro_test():
    msg = "hello world"
    aes = encryption.AESCrypt()
    crypted = aes.encrypt(msg)
    decrypted = aes.decrypt(aes.getKey(), crypted)
    #print(crypted)
    #print(decrypted)
    assert (decrypted == msg), 'Decryption fail!'
"""

import client
import server
from threading import Thread

TEST_MESSAGE = "Hello, World"


def simple_exchange_test():
    srv = server.Server()
    server_thread = Thread(target=srv.run)
    server_thread.start()

    clients = list()
    clients.append(client.Client(nickname="cli1"))
    clients.append(client.Client(nickname="cli2"))

    client[0].send(TEST_MESSAGE)

    srv.stop()
    server_thread.join()


if __name__ == "__main__":
    try:
        simple_exchange_test()

    except AssertionError as e:
        print(e)
