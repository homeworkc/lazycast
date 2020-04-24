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
import subprocess
import argparse
##################### Settings #####################
player_select = 2
# 0: non-RPi systems. (using vlc or gstreamer)
# 1: player1 has lower latency.
# 2: player2 handles still images and sound better.
# 3: omxplayer
sound_output_select = 0
# 0: HDMI sound output
# 1: 3.5mm audio jack output
# 2: alsa
disable_1920_1080_60fps = 1
enable_mouse_keyboard = 1

display_power_management = 0
# 1: (For projectors) Put the display in sleep mode when not in use by lazycast 

####################################################

parser = argparse.ArgumentParser()
parser.add_argument('arg1', nargs='?', default='192.168.173.80')
args = parser.parse_args()
sourceip = vars(args)['arg1']

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (sourceip, 7236)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

connectcounter = 0
while True: 
	try:
		sock.connect(server_address)
	except socket.error, e:
		#connectcounter = connectcounter + 1
		#if connectcounter == 3:
		sock.close()
		sys.exit(1)
	else:
		break

cpuinfo = os.popen('grep Hardware /proc/cpuinfo')
runonpi = 'BCM2835' in cpuinfo.read()
cpuinfo.close()

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
m2data = data


# M3
data=(sock.recv(1000))
print "---M3--->\n" + data

msg = 'wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\n'
if player_select == 2:
	msg = msg + 'wfd_audio_codecs: LPCM 00000002 00\r\n'
else:
	msg = msg + 'wfd_audio_codecs: AAC 00000001 00\r\n'

if disable_1920_1080_60fps == 1:
	msg = msg + 'wfd_video_formats: 00 00 02 10 0001FEFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'
else:
	msg = msg + 'wfd_video_formats: 00 00 02 10 0001FFFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'

msg = msg +'wfd_3d_video_formats: none\r\n'\
	+'wfd_coupled_sink: none\r\n'\
	+'wfd_connector_type: 05\r\n'\
	+'wfd_uibc_capability: input_category_list=GENERIC, HIDC;generic_cap_list=Keyboard, Mouse;hidc_cap_list=Keyboard/USB, Mouse/USB;port=none\r\n'\
	+'wfd_standby_resume_capability: none\r\n'\
	+'wfd_content_protection: none\r\n'


if runonpi and not os.path.exists('edid.txt'):
		os.system('tvservice -d edid.txt')

edidlen = 0
if os.path.exists('edid.txt'):
	edidfile = open('edid.txt','r')
	lines = edidfile.readlines()
	edidfile.close()
	edidstr =''
	for line in lines:
		edidstr = edidstr + line
	edidlen = len(edidstr)

if 'wfd_display_edid' in data and edidlen != 0:
	msg = msg + 'wfd_display_edid: ' + '{:04X}'.format(edidlen/256) + ' ' + str(edidstr.encode('hex'))+'\r\n'

if 'microsoft_latency_management_capability' in data:
	msg = msg + 'microsoft-latency-management-capability: supported\r\n'
if 'microsoft_format_change_capability' in data:
	msg = msg + 'microsoft_format_change_capability: supported\r\n'

# if 'intel_friendly_name' in data:
# 	msg = msg + 'intel_friendly_name: raspberrypi\r\n'


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
					os.system('./control/controlhidc.bin '+ uibcport + ' ' + sourceip + ' &')
				elif('generic_cap_list=none' not in entry):
					os.system('./control/control.bin '+ uibcport + ' &')

uibcstart(sock,data)

def killall(control):
        os.system('pkill vlc')
        os.system('pkill cvlc')
        os.system('pkill gst-launch-1.0')
        os.system('pkill player.bin')
        os.system('pkill h264.bin')
        if display_power_management == 1:
                os.system('vcgencmd display_power 0')
        if control:
                os.system('pkill control.bin')
                os.system('pkill controlhidc.bin')

# M5
data=(sock.recv(1000))
print "---M5--->\n" + data

s_data = 'RTSP/1.0 200 OK\r\nCSeq: 4\r\n\r\n'
print "<--------\n" + s_data
sock.sendall(s_data)


# M6
m6req ='SETUP rtsp://'+sourceip+'/wfd1.0/streamid=0 RTSP/1.0\r\n'\
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
m7req ='PLAY rtsp://'+sourceip+'/wfd1.0/streamid=0 RTSP/1.0\r\n'\
+'CSeq: 102\r\n'\
+'Session: '+str(sessionid)+'\r\n\r\n'
print "<---M7---\n" + m7req
sock.sendall(m7req)

data=(sock.recv(1000))
print "-------->\n" + data

print "---- Negotiation successful ----"


if not runonpi:
	player_select = 0

def launchplayer(player_select):
	killall(False)
        if display_power_management == 1:
                os.system('vcgencmd display_power 1')
	if player_select == 0:
		# os.system('gst-launch-1.0 -v udpsrc port=1028 ! application/x-rtp,media=video,encoding-name=H264 ! queue ! rtph264depay ! avdec_h264 ! autovideosink &')
		# os.system('gst-launch-1.0 -v udpsrc port=1028 ! video/mpegts ! tsdemux !  h264parse ! queue ! avdec_h264 ! ximagesink sync=false &')
		# os.system('gst-launch-1.0  -v  playbin   uri=udp://0.0.0.0:1028/wfd1.0/streamid=0  video-sink=ximagesink audio-sink=alsasink sync=false &')
		# os.system('gst-launch-1.0  -v  playbin   uri=udp://0.0.0.0:1028/wfd1.0/streamid=0  video-sink=xvimagesink audio-sink=alsasink sync=false &')
		if False: # Change False to True if you want to use gstreamer
			os.system('gst-launch-1.0  -v  playbin   uri=udp://0.0.0.0:1028/wfd1.0/streamid=0  video-sink=autovideosink audio-sink=alsasink sync=false &')
		else:
			os.system('vlc --fullscreen rtp://0.0.0.0:1028/wfd1.0/streamid=0 --intf dummy --no-ts-trust-pcr --ts-seek-percent --network-caching=300 --no-mouse-events & ')
	elif player_select == 1:
		os.system('./player/player.bin '+str(idrsockport)+' '+str(sound_output_select)+' &')
	elif player_select == 2:
		sinkip = sock.getsockname()[0]
		print sinkip
		print('./h264/h264.bin '+str(idrsockport)+' '+str(sound_output_select)+' '+sinkip+' &')
		os.system('./h264/h264.bin '+str(idrsockport)+' '+str(sound_output_select)+' '+sinkip+' &')
	elif player_select == 3:
		#if 'MSMiracastSource' in m2data:
		#	os.system('omxplayer rtp://0.0.0.0:1028 -n -1 --live &') # For Windows 10 when no sound is playing
		#else:
		#	os.system('omxplayer rtp://0.0.0.0:1028 --live &')
		#os.system('omxplayer rtp://0.0.0.0:1028 -i')
		omxplayerinfo = subprocess.Popen('omxplayer rtp://0.0.0.0:1028 -i'.split(),stderr=subprocess.PIPE).communicate()
		if '0 channels' in omxplayerinfo[1]:
			os.system('omxplayer rtp://0.0.0.0:1028 -n -1 --live &') # For Windows 10 when no sound is playing
		else:
			os.system('omxplayer rtp://0.0.0.0:1028 --live &')

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
					processrunning = os.popen('ps au').read()
					if player_select == 2 and 'h264.bin' not in processrunning:
						launchplayer(player_select)						
						sleep(0.01)
					else:
						watchdog = watchdog + 1
						if watchdog == 70/0.01:
							killall(True)
							sleep(1)
							break
				else:
					sys.exit(1)
			else:
				print datafromc
				elemfromc = datafromc.split(' ')				
				if elemfromc[0] == 'recv':
					killall(True)
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
			killall(True)
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



