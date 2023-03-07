#!/usr/bin/env python3
"""
	This software is part of lazycast, a simple wireless display receiver for Raspberry Pi
	Copyright (C) 2020 Hsun-Wei Cho
	Using any part of the code in commercial products is prohibited.
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import socket
from time import sleep
import os
import uuid
commands = {}
commands[1] = 'SOURCE_READY'
commands[2] = 'STOP_PROJECTION'
commands[3] = 'SECURITY_HANDSHAKE'
commands[4] = 'SESSION_REQUEST'
commands[5] = 'PIN_CHALLENGE'
commands[6] = 'PIN_RESPONSE'

types = {}
types[0] = 'FRIENDLY_NAME'
types[2] = 'RTSP_PORT'
types[3] = 'SOURCE_ID'
types[4] = 'SECURITY_TOKEN'
types[5] = 'SECURITY_OPTIONS'
types[6] = 'PIN_CHALLENGE'
types[7] = 'PIN_RESPONSE_REASON'

if os.path.exists('uuid.txt'):
	uuidfile = open('uuid.txt','r')
	lines = uuidfile.readlines()
	uuidfile.close()
	uuidstr = lines[0]
else:
	uuidstr = str(uuid.uuid4()).upper()
	uuidfile = open('uuid.txt','w')
	uuidfile.write(uuidstr)
	uuidfile.close()

hostname = socket.gethostname() 
print('The hostname of this machine is: '+hostname)

print(uuidstr)

dnsstr = 'avahi-publish-service '+hostname+' _display._tcp 7250 container_id={'+uuidstr+'}'
print(dnsstr)
os.system(dnsstr+' &')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('',7250))
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.listen(1)

while True:
	(conn, addr) = sock.accept()
	print('Connected by', addr)
	sourceip = addr[0]

	
	while True:
		data = conn.recv(1024)
		# print data
		print(data.hex())

		if len(data) == 0:
			break

		
		data = data.hex()
		size = int(data[0:4],16)
		version = int(data[4:6])
		command = int(data[6:8])

		print (size,version,command)
		
		messagetype = commands[command]
		print(messagetype)

		if messagetype == 'SOURCE_READY':
			os.system('./d2.py '+sourceip+' &')


		i = 8
		while i<size:
			tlvtypehex = int(data[i:i+2])
			valuelen = int(data[i+2:i+6],16)
			value = data[i+6:i+6+2*valuelen]
			i = i+6+2*valuelen
			print(tlvtypehex,valuelen)
			tlvtype = types[tlvtypehex]
			print(tlvtype)
			if tlvtype == 'FRIENDLY_NAME':
				print(value)



		# conn.send(data)

	conn.close()

sock.close()
