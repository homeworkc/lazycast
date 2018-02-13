import socket
import binascii
from struct import *


address = ('0.0.0.0', 1028)
rtpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rtpsock.bind(address)

data=(rtpsock.recv(2000))
print binascii.hexlify(data)

data=(rtpsock.recv(2000))
print binascii.hexlify(data)

data=(rtpsock.recv(2000))
print binascii.hexlify(data)
