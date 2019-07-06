from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from hashlib import sha256
from base64 import b64encode, b64decode
from os import urandom

class AESCrypt:
    def __init__(self, key):
        self.key = sha256(key).digest() if isinstance(key, (bytes, bytearray)) else sha256(key.encode('utf-8')).digest()
    
    def pad(self, s):
        return s+b"\0" * (AES.block_size - len(s) % AES.block_size)
    
    def encrypt(self, msg):
        message = self.pad(msg)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(message)

    def encrypt_file(self, path):
        with open(path, 'rb') as file:
            text = file.read()
            file.close()
        enc = self.encrypt(text)
        with open(path, 'wb') as file:
            file.write(enc)
            file.close()
    
    def decrypt(self, encrypted):
        iv = encrypted[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        text = cipher.decrypt(encrypted[AES.block_size:])
        return text.rstrip(b"\0")
    
    def decrypt_file(self, path):
        with open(path, 'rb') as file:
            encrypted = file.read()
            file.close()
        enc = self.decrypt(encrypted)
        with open(path, 'wb') as file:
            file.write(enc)
            file.close()

class RSACrypt:
    def __init__(self, key=None):
        self.__private_key = self.__make_key() if not key else RSA.importKey(key)
    
    def __make_key(self, NOB=1024):
        return RSA.generate(NOB, Random.new().read)
    
    def export_public(self):
        return self.__private_key.publickey().exportKey()
    
    def export_private(self):
        return self.__private_key.exportKey()
    
    def encrypt(self, msg, publickey=None):
        encryptor = PKCS1_OAEP.new(self.__private_key.publickey()) if not publickey else PKCS1_OAEP.new(RSA.importKey(publickey))
        return b64encode(encryptor.encrypt(msg.encode('utf-8')))
    
    def decrypt(self, encrypted, privatekey=None):
        decryptor = PKCS1_OAEP.new(self.__private_key) if not privatekey else PKCS1_OAEP.new(RSA.importKey(privatekey))
        return decryptor.decrypt(b64decode(encrypted)).decode('utf-8')

if __name__ == "__main__":
    rsa_crypt = RSACrypt()
    msg = "hello_woorlllddd."
    encrypted = rsa_crypt.encrypt(msg)
    print("Encrypred: ", encrypted)
    print("Decrypted: ", rsa_crypt.decrypt(encrypted))