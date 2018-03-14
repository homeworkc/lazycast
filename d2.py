#!/usr/bin/env python2

"""
   This software is part of lazycast, a simple wireless display receiver for Raspberry Pi
   Copyright (C) 2018 Hsun-Wei Cho
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
import os
import threading
from threading import Thread
import time
import fcntl
import errno
from time import sleep
import subprocess

errorsignal = 0
class Getplayererr(Thread):
    def __init__(self):
		Thread.__init__(self)
		self.daemon=True
		self.p = subprocess.Popen(["./player.bin"],stderr=subprocess.PIPE)
    def run(self):
		global errorsignal
		while True:
			#print len(p.stderr)#won't work
			ln = self.p.stderr.readline()
			print ln
			if 'PES packet size' in ln or 'max delay reached' in ln:
				lock.acquire()
				errorsignal = 1
				lock.release()


	
	

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('192.168.101.80', 7236)
sock.connect(server_address)

data = (sock.recv(1000))
print data

sock.sendall('RTSP/1.0 200 OK\r\nCSeq: 1\r\n\Public: org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER\r\n\r\n')

sock.sendall('OPTIONS * RTSP/1.0\r\nCSeq: 100\r\nRequire: org.wfa.wfd1.0\r\n\r\n')


data = (sock.recv(1000))
print data

data=(sock.recv(1000))
print data

msg='wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\n'\
+'wfd_audio_codecs: AAC 00000003 00\r\n'\
+'wfd_video_formats: 00 00 02 04 0001FEFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'\
+'wfd_3d_video_formats: none\r\n'\
+'wfd_coupled_sink: none\r\n'\
+'wfd_display_edid: none\r\n'\
+'wfd_connector_type: 05\r\n'\
+'wfd_uibc_capability: input_category_list=GENERIC, HIDC;generic_cap_list=Keyboard, Mouse, MultiTouch;hidc_cap_list=Keyboard/USB, Mouse/USB;port=none\r\n'\
+'wfd_standby_resume_capability: none\r\n'\
+'wfd_content_protection: none\r\n'
'''
+'intel_sink_version: none\r\n'\
+'intel_sink_information: 05\r\n'\
+'intel_lower_bandwidth: none\r\n'\
+'intel_interactivity_mode: none\r\n'\
+'intel_fast_cursor: none\r\n'
'''




m3resp ='RTSP/1.0 200 OK\r\nCSeq: 2\r\n'+'Content-Type: text/parameters\r\nContent-Length: '+str(len(msg))+'\r\n\r\n'+msg
print m3resp
sock.sendall(m3resp)

print 'm3 success\n'


data=(sock.recv(1000))
print data
sock.sendall('RTSP/1.0 200 OK\r\nCSeq: 3\r\n\r\n')

print 'm4 success\n'

data=(sock.recv(1000))
print data
sock.sendall('RTSP/1.0 200 OK\r\nCSeq: 4\r\n\r\n')

print 'm5 success\n'

m6req ='SETUP rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n'\
+'CSeq: 101\r\n'\
+'Transport: RTP/AVP/UDP;unicast;client_port=1028\r\n\r\n'
print m6req

sock.sendall(m6req)
data=(sock.recv(1000))
print data

paralist=data.split(';')
print paralist
serverport=[x for x in paralist if 'server_port=' in x]
print serverport
serverport=serverport[-1]
serverport=serverport[12:17]
print serverport

paralist=data.split( )
position=paralist.index('Session:')+1
sessionid=paralist[position]

print 'm6 success\n'


m7req ='PLAY rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n'\
+'CSeq: 102\r\n'\
+'Session: '+str(sessionid)+'\r\n\r\n'
print m7req

sock.sendall(m7req)
data=(sock.recv(1000))
print data


if (os.uname()[-1][:4]=="armv"):
	#use this on Pi
	os.system('pkill omxplayer')
	os.system('sleep 2')
	#os.system('omxplayer -b rtp://0.0.0.0:1028/wfd1.0/streamid=0 --live &')
else:
	os.system('vlc --fullscreen rtp://0.0.0.0:1028/wfd1.0/streamid=0 &')
	#if vlc is used, use aac +'wfd_audio_codecs: AAC 00000001 00\r\n'\


fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)


lock = threading.RLock()



getplayererr = Getplayererr()
getplayererr.start()

csnum = 102
while True:

	try:
		data=(sock.recv(1000))
	except socket.error, e:
		err = e.args[0]
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			
			if(errorsignal==1):
				csnum = csnum + 1
				msg = 'wfd-idr-request'
				idrreq ='SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n'\
				+'Content-Length: '+str(len(msg))+'\r\n'\
				+'Content-Type: text/parameters\r\n'\
				+'CSeq: '+str(csnum)+'\r\n\r\n'\
				+msg


				print idrreq

				sock.sendall(idrreq)

				lock.acquire()
				errorsignal=0	
				lock.release()
			continue
		else:
			print e
			sys.exit(1)
	else:
		
		print data
		paralist=data.split('\r')
		tmp=[x for x in paralist if 'CSeq' in x]

		if 'RTSP/1.0 200 OK' in data:
			continue
		elif (len(tmp)==0):
			break
		
		for cseq in tmp:
			resp='RTSP/1.0 200 OK\r'+cseq+'\r\n\r\n';#cseq contains \n
			print resp
			sock.sendall(resp)

		
sock.close()

