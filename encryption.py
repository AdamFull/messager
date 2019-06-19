from Crypto import Random
from Crypto.Cipher import AES
import hashlib

class AESCrypt:
    def __init__(self, key):
        self.key = hashlib.sha256(key).digest()
    
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
        return text.rstrip(b"\0").decode('utf-8')
    
    def decrypt_file(self, path):
        with open(path, 'rb') as file:
            encrypted = file.read()
            file.close()
        enc = self.decrypt(encrypted)
        with open(path, 'wb') as file:
            file.write(enc)
            file.close()