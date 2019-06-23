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
import time

TEST_MESSAGE = "Hello, World"
message_queue = list()


def store_messages(raw_data):
    print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))
    message_queue.append(raw_data)


def simple_exchange_test():
    srv = server.Server()
    server_thread = Thread(target=srv.run)
    server_thread.start()

    cli1 = client.Client(nickname="cli1", receive_callback=store_messages)
    cli2 = client.Client(nickname="cli2", receive_callback=store_messages)

    message_queue.clear()

    time.sleep(1.0)
    cli1.send(TEST_MESSAGE)
    #TODO compare recieved messages

    srv.stop()
    server_thread.join()


if __name__ == "__main__":
    try:
        simple_exchange_test()

    except AssertionError as e:
        print(e)
