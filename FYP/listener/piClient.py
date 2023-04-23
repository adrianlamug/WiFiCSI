import socket

UDP_IP = "255.255.255.255"
UDP_PORT = 5500

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:

    sock.bind((UDP_IP, UDP_PORT))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_pc:
        server_pc.connect(('169.254.103.233', 5501))

        while True:
            try:
                data, addr = sock.recvfrom(512 * 4)  # buffer size is 2048 + 18 bytes
                server_pc.sendall(data)
            except ConnectionError as e:
                decision = input("Server disconnected. Reconnect? (Y/N)")
                if decision in ["n", "N"]:
                    exit(0)
                else:
                    continue

