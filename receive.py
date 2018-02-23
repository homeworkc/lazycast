import socket
import binascii
from struct import *


address = ('0.0.0.0', 1028)
rtpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rtpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
rtpsock.bind(address)
file=open("win10data.ts","w")
while 1:
	data=(rtpsock.recv(2000))
	tsdata=data[12:len(data)]
	file.write(tsdata)
	print data[0:12]
file.close()

