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
        '''The method puts a digital signature on the message.'''
        signer = PKCS1_v1_5.new(self.private_rsa_key)
        digest = SHA256.new(data.encode())
        return b64encode(signer.sign(digest))
    
    def verify(self, data, sign, public_key, sock=None):
        '''The method verifies the client’s digital signature,\n
        if the signature has passed verification, the message remains,\n
        otherwise the client’s socket is closed.'''
        signer = PKCS1_v1_5.new(RSA.importKey(public_key))
        digest = SHA256.new(data.encode())
        if signer.verify(digest, b64decode(sign)):
            return loads(data)
        else:
            sock.close()
    
    def request(self, information, sock):
        byte_string = dumps(information, ensure_ascii=False).encode()
        data = struct.pack('>I', len(byte_string)) + byte_string
        sock.sendall(data)
    
    def response(self, sock):
        raw_msglen = self.recvall(4, sock)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        data = self.recvall(msglen, sock)
        if data:
            return loads(data.decode())
        else:
            return None
    
    def send(self, information, sock):
        '''The method of sending messages.\n
        Can encrypt messages before sending, or not encrypt.'''
        byte_string = AESCrypt(self.aes_key).encrypt(dumps(information).encode())
        data = struct.pack('>I', len(byte_string)) + byte_string
        sock.sendall(data)
    
    def sendws(self, information, sock):
        '''The method of sending messages with a digital signature.\n
        When sending a message, it adds the signature and public key of the sender.'''
        data = dumps(information, ensure_ascii=False)
        if not "sign" in information.keys():
            information = ({
                    "data": data,
                    "sign": self.sign(data).decode(), 
                    "rsa": self.RSA.export_public().decode()})
        self.send(information, sock)

    def recv(self, sock):
        '''The method of receiving messages.\n
            This method can receive messages using and without encryption.'''
        raw_msglen = self.recvall(4, sock)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        data = self.recvall(msglen, sock)
        if data:
            return loads(AESCrypt(self.aes_key).decrypt(data).decode())
        else:
            return None
    
    def recvwv(self, sock):
        '''The method of receiving messages with an digital signature.\n
        Upon receipt, the signature is verified, and if it matches,\n
        the message is converted to readable, otherwise the user will be kicked out of the server.'''
        data = self.recv(sock)
        return self.verify(data["data"], data["sign"], data["rsa"], sock)

    def recvall(self, n, sock):
        '''A helper method for accepting messages,\n
        first reading bytes from the socket, and then the message.'''
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data