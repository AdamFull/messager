import base64
from Crypto import Random
from Crypto.Cipher import AES

pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
unpad = lambda s : s[0:-ord(s[-1])]

class AESCrypt:
    def __init__(self):
        self.key = 'qwertyuiopasdfgh'
    
    def getKey(self):
        return self.key
    
    def encrypt(self, message):
        raw = pad(message)
        iv = Random.new().read(AES.block_size)
        aes = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + aes.encrypt(raw))
    
    def decrypt(self, key, message):
        raw = base64.b64decode(message)
        iv = raw[:16]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return unpad(aes.decrypt(raw[16:]))