import struct
from hashlib import sha256
from json import dumps, loads
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64encode, b64decode, decodebytes
from random import choice
from string import ascii_letters, digits, punctuation
import binascii

class AESCrypt:
    def __init__(self, key):
        self.key = sha256(key.encode('utf-8')).digest()
    
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
        return b64encode(encryptor.encrypt(msg.encode('utf-8')))
    
    def decrypt(self, encrypted, privatekey=None):
        decryptor = PKCS1_OAEP.new(self.private_key) if not privatekey else PKCS1_OAEP.new(RSA.importKey(privatekey))
        return decryptor.decrypt(b64decode(encrypted)).decode('utf-8')

class Protocol:
    def __init__(self):
        self.aes_key = sha256(''.join(choice(ascii_letters+punctuation+digits) for i in range(32)).encode('utf-8')).hexdigest()
        self.RSA = None
        self.private_rsa_key = None
        self.public_rsa_key = None
    
    def load_rsa(self, private_key):
        self.RSA = RSACrypt(private_key)
        self.private_rsa_key = self.RSA.private_key
        self.public_rsa_key = self.private_rsa_key.publickey()
    
    def sign(self, data):
        signer = PKCS1_v1_5.new(self.private_rsa_key)
        digest = SHA256.new()
        try:
            digest.update(b64decode(data))
        except binascii.Error:
            digest.update(data.encode())
        return b64encode(signer.sign(digest))
    
    def verify(self, data, sign, public_key):
        signer = PKCS1_v1_5.new(RSA.importKey(public_key))
        digest = SHA256.new()
        digest.update(b64encode(data.encode()))
        if signer.verify(digest, b64decode(sign)):
            return dumps(data)
        else:
            return None
    
    def send(self, string, sock, crypt=False):
        information = string
        if not "sign" in information.keys():
            information = ({
                "data": dumps(information, ensure_ascii=False),
                "sign": self.sign(dumps(information, ensure_ascii=False)).decode(), 
                "rsa": self.RSA.export_public().decode()})
        byte_string = dumps(information, ensure_ascii=False).encode('utf-8')
        if crypt:
            byte_string = AESCrypt(self.aes_key).encrypt(byte_string)
        data = struct.pack('>I', len(byte_string)) + byte_string
        sock.sendall(data)

    def recv(self, sock, crypt=False): #Message receiving method
        raw_msglen = self.recvall(4, sock)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        data = self.recvall(msglen, sock)
        if data:
            if crypt:
                return loads(AESCrypt(self.aes_key).decrypt(data).decode('utf-8'))
            else:
                data = loads(data.decode('utf-8'))
                return self.verify(data["data"], data["sign"], data["rsa"])
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