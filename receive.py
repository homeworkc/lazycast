import socket
import binascii
from struct import *


address = ('0.0.0.0', 1028)
rtpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rtpsock.bind(address)
while 1:
    data=(rtpsock.recv(2000))
    tsdata=data[8:len(data)]
    print ord(tsdata[0:1])
#    print binascii.hexlify(data)


