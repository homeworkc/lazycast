#!/usr/bin/python

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
import time

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
+'wfd_audio_codecs: LPCM 00000003 00\r\n'\
+'wfd_video_formats: 00 00 01 04 0001FFFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'\
+'wfd_3d_video_formats: none\r\n'\
+'wfd_coupled_sink: none\r\n'\
+'wfd_display_edid: none\r\n'\
+'wfd_connector_type: 05\r\n'\
+'wfd_uibc_capability: none\r\n'\
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

'''
#use this on Pi
os.system('pkill omxplayer')
os.system('sleep 1; omxplayer -b --avdict rtsp_transport:tcp rtp://192.168.101.80:1028/wfd1.0/streamid=0 --live --threshold 0.05 --timeout 10000 &')
'''

os.system('vlc --fullscreen rtp://0.0.0.0:1028/wfd1.0/streamid=0 &')



while True:
	data=(sock.recv(1000))
	print data
	paralist=data.split('\r')
	tmp=[x for x in paralist if 'CSeq' in x]
	cseq=tmp[-1]
	resp='RTSP/1.0 200 OK\r'+cseq+'\r\n\r\n';#cseq contains \n
	print resp
	if paralist[0]=='GET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0':
		sock.sendall(resp)
	elif paralist[0]=='SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0':
		sock.sendall(resp)

		
sock.close()

