# import socket

# target_host = "www.google.com"
# target_port = 80

# client =socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# client.connect((target_host, target_port))

# client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# response = client.recv(4096)

# print(response.decode())

# client.close()

import socket
import ssl

host = "www.google.com"
port = 443

context = ssl.create_default_context()
client = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=host)

client.connect((host, port))
client.send(b"GET / HTTP/1.1\r\nHost: www.google.com\r\nConnection: close\r\n\r\n")

# response =  client.recv(4096)

data = b""
while True:
    chunk = client.recv(4096)
    if not chunk:
        break
    data += chunk

print(data.decode(errors="ignore"))
client.close()