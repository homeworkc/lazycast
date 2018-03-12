import socket
import binascii
import time
from struct import *



address = ('0.0.0.0', 1028)
rtpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
rtpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
rtpsock.bind(address)
file=open("win10data.ts","w")

address = ('0.0.0.0', 59823)
outsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


cc11file=open("cc11.bin")
cc12file=open("cc12.bin")
cc13file=open("cc13.bin")

cc11=cc11file.read(188)
cc12=cc12file.read(188)
cc13=cc13file.read(188)

sendblankaudio=False
oldtime=time.time()

cc11timestamp=cc11[13:18]
print binascii.hexlify(cc11timestamp)
audiocc=0;
print binascii.hexlify(cc11[3])
print binascii.hexlify(cc12[3])
print binascii.hexlify(cc13[3])

while 1:
	data = (rtpsock.recv(2000))
	datalen = len(data)
	numofts = (datalen-12)/188

	timestamp = data[4:8]
	print binascii.hexlify(timestamp)
	

	for i in range(12,datalen,188):
		#print data[i+1]
		if(data[i+1]=="Q"): # data[i:i+3] #audio is 0x475100 
			oldtime=time.time()
		else:
			currenttime=time.time()
			if(currenttime-oldtime>0.2):
				sendblankaudio=True
				oldtime=currenttime

	if(sendblankaudio and datalen<952):#at least 3 ts block
		print len(data)





		data=data+cc11+cc12+cc13
		print len(data)
		sendblankaudio=False
		print "sent!!!!!!!"
	#print binascii.hexlify(data[0:2])
	
	
	
	
	outsock.sendto(data,address)
#	tsdata=data[12:len(data)]
#	file.write(tsdata)
#	print data[12]
file.close()

