#!/usr/bin/env python2
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

commands = {}
commands['01'] = 'SOURCE_READY'
commands['02'] = 'STOP_PROJECTION'
commands['03'] = 'SECURITY_HANDSHAKE'
commands['04'] = 'SESSION_REQUEST'
commands['05'] = 'PIN_CHALLENGE'
commands['06'] = 'PIN_RESPONSE'

types = {}
types['00'] = 'FRIENDLY_NAME'
types['02'] = 'RTSP_PORT'
types['03'] = 'SOURCE_ID'
types['04'] = 'SECURITY_TOKEN'
types['05'] = 'SECURITY_OPTIONS'
types['06'] = 'PIN_CHALLENGE'
types['07'] = 'PIN_RESPONSE_REASON'



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
		print data.encode('hex')

		if data == '':
			break

		size = int(data[0:2].encode('hex'),16)
		version = data[2].encode('hex')
		command = data[3].encode('hex')

		print (size,version,command)
		
		messagetype = commands[command]
		print messagetype

		if messagetype == 'SOURCE_READY':
			os.system('./d2.py '+sourceip+' &')


		i = 4
		while i<size:
			tlvtypehex = data[i].encode('hex')
			valuelen = int(data[i+1:i+3].encode('hex'),16)
			value = data[i+3:i+3+valuelen]
			i = i+3+valuelen
			print (tlvtypehex,valuelen)
			tlvtype = types[tlvtypehex]
			print tlvtype,
			if tlvtype == 'FRIENDLY_NAME':
				print value


		# conn.send(data)

	conn.close()

sock.close()

