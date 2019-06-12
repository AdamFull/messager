#!/usr/bin/python3
# -*- coding: utf-8 -*-

import encryption

def crypro_test():
    msg = "hello world"
    aes = encryption.AESCrypt()
    crypted = aes.encrypt(msg)
    decrypted = aes.decrypt(aes.getKey(), crypted)
    #print(crypted)
    #print(decrypted)
    assert (decrypted == msg), 'Decryption fail!'


if __name__ == "__main__":
    try:
        crypro_test()

    except AssertionError as e:
        print(e)
