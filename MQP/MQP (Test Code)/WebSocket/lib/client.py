from websocket import create_connection
from time import sleep

ws = create_connection("ws://localhost:8080")
while(True):
    ws.send("Hello")
    sleep(1)