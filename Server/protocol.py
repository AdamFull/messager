import struct
from json import dumps, loads
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from hashlib import sha256
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64encode, b64decode
from random import choice
from string import ascii_letters, digits, punctuation

class AESCrypt:
    def __init__(self, key):
        self.key = sha256(key.encode()).digest()
    
    def pad(self, s):
        return s+b"\0" * (AES.block_size - len(s) % AES.block_size)
    
    def encrypt(self, msg):
        message = self.pad(msg)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(message)
    
    def decrypt(self, encrypted):
        iv = encrypted[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        text = cipher.decrypt(encrypted[AES.block_size:])
        return text.rstrip(b"\0")

class RSACrypt:
    def __init__(self, key=None):
        self.private_key = self.make_key() if not key else RSA.importKey(key)
    
    def make_key(self, NOB=1024):
        return RSA.generate(NOB, Random.new().read)
    
    def export_public(self):
        return self.private_key.publickey().exportKey()
    
    def export_private(self):
        return self.private_key.exportKey()
    
    def encrypt(self, msg, publickey=None):
        encryptor = PKCS1_OAEP.new(self.private_key.publickey()) if not publickey else PKCS1_OAEP.new(RSA.importKey(publickey))
        return b64encode(encryptor.encrypt(msg.encode()))
    
    def decrypt(self, encrypted, privatekey=None):
        decryptor = PKCS1_OAEP.new(self.private_key) if not privatekey else PKCS1_OAEP.new(RSA.importKey(privatekey))
        return decryptor.decrypt(b64decode(encrypted)).decode()

class Protocol:
    def __init__(self):
        self.aes_key = sha256(''.join(choice(ascii_letters+punctuation+digits) for i in range(32)).encode()).hexdigest()
        self.RSA = None
        self.private_rsa_key = None
        self.public_rsa_key = None
    
    def load_rsa(self, private_key):
        self.RSA = RSACrypt(private_key)
        self.private_rsa_key = self.RSA.private_key
        self.public_rsa_key = self.private_rsa_key.publickey()
    
    def sign(self, data):
        signer = PKCS1_v1_5.new(self.private_rsa_key)
        digest = SHA256.new(data.encode())
        sign = b64encode(signer.sign(digest))
        return sign
    
    def verify(self, data, sign, public_key, rsa=False):
        signer = PKCS1_v1_5.new(RSA.importKey(public_key))
        digest = SHA256.new(data.encode())
        if signer.verify(digest, b64decode(sign)):
            return loads(data)
        else:
            return None
    
    def send(self, information, sock, aes=False, rsa=False):
        if not "sign" in information.keys():
            data = self.RSA.encrypt(dumps(information, ensure_ascii=False)) if rsa else dumps(information, ensure_ascii=False)
            information = ({
                "data": data,
                "sign": self.sign(data).decode(), 
                "rsa": self.RSA.export_public().decode()})
        byte_string = dumps(information).encode()
        if aes:
            byte_string = AESCrypt(self.aes_key).encrypt(byte_string)
        data = struct.pack('>I', len(byte_string)) + byte_string
        sock.sendall(data)

    def recv(self, sock, aes=False): #Message receiving method
        raw_msglen = self.recvall(4, sock)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        data = self.recvall(msglen, sock)
        if data:
            if aes:
                data = loads(AESCrypt(self.aes_key).decrypt(data).decode())
                return data
            else:
                data = loads(data.decode())
                return data
        else:
            return None

    def recvall(self, n, sock): #Вспомогательный метод для принятия сообщений, читает из сокета
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data