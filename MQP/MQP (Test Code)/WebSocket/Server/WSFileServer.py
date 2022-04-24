import socket
import os

# device's ip
SERVER_HOST = "localhost"
SERVER_PORT = 8080

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096

RECVNAME = "data.json"

## setup websocket
#create the server socket
s = socket.socket()

# bind the socket to our local address
s.bind((SERVER_HOST, SERVER_PORT))

# enable our server to accept connections
# the system will allow 5 unaccepted connections before refusing new ones
s.listen(5)
print(f"[+] Listening as {SERVER_HOST}:{SERVER_PORT}")

# accept connection if any
client_socket, address = s.accept()

# if the code below is executed, that means that the sender is connected
print(f"[+] {address} is connected")


## receive the file infos
# receive using client socket, not server socket
# filename = client_socket.recv(BUFFER_SIZE).decode()

#remove absolute path if there is one
# filename = os.path.basename(filename)


## start receiving the file
with open(RECVNAME, "wb") as f:
    while(True):
        # read 1024 bytes from the socket (receive)
        bytes_read = client_socket.recv(BUFFER_SIZE)

        if not bytes_read:
            # nothing is received
            # transmission is finished
            break
        
        # write to the file the bytes we just received
        f.write(bytes_read)


## close the sockets
client_socket.close()
s.close()
