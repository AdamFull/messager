import struct

class Protocol:
    def __init__(self):
        pass
    
    def send(self, string, sock):
        if not isinstance(string, (bytes, bytearray)):
            byte_string = string.encode('utf-8')
        else:
            byte_string = string
        data = struct.pack('>I', len(byte_string)) + byte_string
        sock.sendall(data)

    def recv(self, sock): #Message receiving method
        raw_msglen = self.recvall(4, sock)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.recvall(msglen, sock)

    def recvall(self, n, sock): #Вспомогательный метод для принятия сообщений, читает из сокета
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data