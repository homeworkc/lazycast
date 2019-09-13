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
import fcntl, os
import errno
import threading
from threading import Thread
import time
from time import sleep
import sys
##################### Settings #####################
player_select = 2
# 0: non-RPi systems. (using vlc)
# 1: player1 has lower latency.
# 2: player2 handles still images and sound better.
sound_output_select = 0
# 0: HDMI sound output
# 1: 3.5mm audio jack output
# 2: alsa
disable_1920_1080_60fps = 1
enable_mouse_keyboard = 1

####################################################

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('192.168.173.80', 7236)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

connectcounter = 0
while True: 
	try:
		sock.connect(server_address)
	except socket.error, e:
		connectcounter = connectcounter + 1
		if connectcounter == 20:
			sock.close()
			sys.exit(1)
	else:
		break

idrsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
idrsock_address = ('127.0.0.1', 0)
idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
idrsock.bind(idrsock_address)
addr, idrsockport = idrsock.getsockname()

data = (sock.recv(1000))
print "---M1--->\n" + data
s_data = 'RTSP/1.0 200 OK\r\nCSeq: 1\r\n\Public: org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER\r\n\r\n'
print "<--------\n" + s_data
sock.sendall(s_data)


# M2
s_data = 'OPTIONS * RTSP/1.0\r\nCSeq: 100\r\nRequire: org.wfa.wfd1.0\r\n\r\n'
print "<---M2---\n" + s_data
sock.sendall(s_data)

data = (sock.recv(1000))
print "-------->\n" + data


# M3
data=(sock.recv(1000))
print "---M3--->\n" + data

msg = 'wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\n'
if player_select == 2:
	msg = msg + 'wfd_audio_codecs: LPCM 00000002 00\r\n'
else:
	msg = msg + 'wfd_audio_codecs: AAC 00000001 00\r\n'

if disable_1920_1080_60fps == 1:
	msg = msg + 'wfd_video_formats: 00 00 02 04 0001FEFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'
else:
	msg = msg + 'wfd_video_formats: 00 00 02 04 0001FFFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'

msg = msg +'wfd_3d_video_formats: none\r\n'\
	+'wfd_coupled_sink: none\r\n'\
	+'wfd_display_edid: none\r\n'\
	+'wfd_connector_type: 05\r\n'\
	+'wfd_uibc_capability: input_category_list=GENERIC, HIDC;generic_cap_list=Keyboard, Mouse;hidc_cap_list=Keyboard/USB, Mouse/USB;port=none\r\n'\
	+'wfd_standby_resume_capability: none\r\n'\
	+'wfd_content_protection: none\r\n'


m3resp ='RTSP/1.0 200 OK\r\nCSeq: 2\r\n'+'Content-Type: text/parameters\r\nContent-Length: '+str(len(msg))+'\r\n\r\n'+msg
print "<--------\n" + m3resp
sock.sendall(m3resp)


# M4
data=(sock.recv(1000))
print "---M4--->\n" + data

s_data = 'RTSP/1.0 200 OK\r\nCSeq: 3\r\n\r\n'
print "<--------\n" + s_data
sock.sendall(s_data)

def uibcstart(sock, data):
	#print data
	messagelist=data.split('\r\n\r\n')
	for entry in messagelist:
		if 'wfd_uibc_capability:' in entry:
			entrylist = entry.split(';')
			uibcport = entrylist[-1]
			uibcport = uibcport.split('\r')
			uibcport = uibcport[0]
			uibcport = uibcport.split('=')
			uibcport = uibcport[1]
			print 'uibcport:'+uibcport+"\n"
			if 'none' not in uibcport and enable_mouse_keyboard == 1:
				os.system('pkill control.bin')
				os.system('pkill controlhidc.bin')
				if('hidc_cap_list=none' not in entry):
					os.system('./control/controlhidc.bin '+ uibcport + ' &')
				elif('generic_cap_list=none' not in entry):
					os.system('./control/control.bin '+ uibcport + ' &')

uibcstart(sock,data)


# M5
data=(sock.recv(1000))
print "---M5--->\n" + data

s_data = 'RTSP/1.0 200 OK\r\nCSeq: 4\r\n\r\n'
print "<--------\n" + s_data
sock.sendall(s_data)


# M6
m6req ='SETUP rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n'\
+'CSeq: 101\r\n'\
+'Transport: RTP/AVP/UDP;unicast;client_port=1028\r\n\r\n'
print "<---M6---\n" + m6req
sock.sendall(m6req)

data=(sock.recv(1000))
print "-------->\n" + data

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


# M7
m7req ='PLAY rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n'\
+'CSeq: 102\r\n'\
+'Session: '+str(sessionid)+'\r\n\r\n'
print "<---M7---\n" + m7req
sock.sendall(m7req)

data=(sock.recv(1000))
print "-------->\n" + data

print "---- Negotiation successful ----"


if (os.uname()[-1][:4] != "armv"):
	player_select = 0

def launchplayer(player_select):
	os.system('pkill vlc')
	os.system('pkill player.bin')
	os.system('pkill h264.bin')
	if player_select == 0:
		os.system('vlc --fullscreen rtp://0.0.0.0:1028/wfd1.0/streamid=0 &')
	elif player_select == 1:
		os.system('./player/player.bin '+str(idrsockport)+' '+str(sound_output_select)+' &')
	elif player_select == 2:
		os.system('./h264/h264.bin '+str(idrsockport)+' '+str(sound_output_select)+' &')
	elif player_select == 3:
		os.system('omxplayer rtp://0.0.0.0:1028 -n -1 --live &')

launchplayer(player_select)

fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
fcntl.fcntl(idrsock, fcntl.F_SETFL, os.O_NONBLOCK)

csnum = 102
watchdog = 0
while True:
	try:
		data = (sock.recv(1000))
	except socket.error, e:
		err = e.args[0]
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			try:
				datafromc = idrsock.recv(1000)
			except socket.error, e:
				err = e.args[0]
				if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
					sleep(0.01)
					watchdog = watchdog + 1
					if watchdog == 70/0.01:
						os.system('pkill control.bin')
						os.system('pkill controlhidc.bin')
						os.system('pkill vlc')
						os.system('pkill player.bin')
						os.system('pkill h264.bin')
						sleep(1)
						break
				else:
					sys.exit(1)
			else:
				print 'ags8jgajdgkajsdlfj;asdkfasdf'+datafromc
				elemfromc = datafromc.split(' ')				
				if elemfromc[0] == 'recv':
					os.system('pkill control.bin')
					os.system('pkill controlhidc.bin')
					os.system('pkill vlc')
					os.system('pkill player.bin')
					os.system('pkill h264.bin')
					sleep(1)
					break
				else:
					csnum = csnum + 1
					msg = 'wfd-idr-request\r\n'
					idrreq ='SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n'\
					+'Content-Length: '+str(len(msg))+'\r\n'\
					+'Content-Type: text/parameters\r\n'\
					+'CSeq: '+str(csnum)+'\r\n\r\n'\
					+msg
	
					print idrreq
					sock.sendall(idrreq)

		else:
			sys.exit(1)
	else:
		print data
		watchdog = 0
		if len(data)==0 or 'wfd_trigger_method: TEARDOWN' in data:
			os.system('pkill control.bin')
			os.system('pkill controlhidc.bin')
			os.system('pkill vlc')
			os.system('pkill player.bin')
			os.system('pkill h264.bin')
			sleep(1)
			break
		elif 'wfd_video_formats' in data:
			launchplayer(player_select)
		messagelist=data.split('\r\n\r\n')
		print messagelist
		singlemessagelist=[x for x in messagelist if ('GET_PARAMETER' in x or 'SET_PARAMETER' in x )]
		print singlemessagelist
		for singlemessage in singlemessagelist:
			entrylist=singlemessage.split('\r')
			for entry in entrylist:
				if 'CSeq' in entry:
					cseq = entry

			resp='RTSP/1.0 200 OK\r'+cseq+'\r\n\r\n';#cseq contains \n
			print resp
			sock.sendall(resp)
		
		uibcstart(sock,data)

idrsock.close()
sock.close()



