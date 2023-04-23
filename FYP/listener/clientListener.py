import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# if using draft2 use this
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind(('192.168.1.228', 2222))
# sock.bind(('169.254.103.233', 2222))
# sock.bind(('169.254.177.92', 2223))
sock.listen(1)
while True:
    print("Now listening....")

    connection, address = sock.accept()
    print("Connection from: " + str(address))

    with open('output.pcap', 'wb') as f:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            f.write(data)
            print("written")
        f.close()

    connection.close()
sock.close()


