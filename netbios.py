import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 137))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
while True:
    data, addr = sock.recvfrom(1024)
    print data
    print addr
    print len(data)
    print data.encode('hex')
