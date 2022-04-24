from websocket import create_connection
import os

BUFFER_SIZE = 4096 # send 4096 bytes each time step

# the ip address and port of the server (receiver)
host = "localhost" # in production this will be spectrumobservatory.wpi.edu
port = 8000          # ws port is typically port 80

# the name and file being sent over the socket
filename = input("Enter the name of the file to transfer:")

# create the client socket
s = create_connection("ws://localhost:8080")

# start sending the file
with open(filename, "rb") as f:
    bytes_read = f.read()
    s.send(bytes_read)

# close the socket
s.close()
