import socket
import subprocess
# RAN ON RASPBERRY PI 3B+
count = 0
while count<500:
    tcpdump_process = subprocess.Popen(['sudo', 'tcpdump', '-i', 'wlan0', 'dst', 'port',
                                    '5500', '-vv', '-w', 'output.pcap', '-c', '1'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in tcpdump_process.stdout:
        print(line)

    tcpdump_error = tcpdump_process.communicate()[1]

    if tcpdump_process.returncode == 0:
        with open("output.pcap", "rb") as f:
            packets = f.read()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('169.254.103.233', 1234))
        sock.sendall(packets)
        sock.close()
        print("tcpdump ran successfully")
        count+=1

    else:
        print('tcpdump encountered an error:\n', tcpdump_error)


# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
# server_address = ('0.0.0.0', 5501)
# sock.bind(server_address)
#
# print("Listening for UDP packets on port {}...".format(server_address[1]))
#
# while True:
#     data, address = sock.recvfrom(4096)
#
#     print("Received {} bytes from {}: {}".format(len(data, address, data)))
#
# def my_server():
