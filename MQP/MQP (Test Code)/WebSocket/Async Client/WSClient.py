import socket

class WebSocketClient():

    def __init__(self):
        pass

    async def connect(self):
        self.s = socket.socket()
        self.s.connect(("localhost", 8080))
        print('[+] Socket Connected')
        return self.s

    async def close(self):
        self.s.close()
