#!/usr/bin/env python3

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
# 3: omxplayer # Using this option for video playback on Android
sound_output_select = 0
# 0: HDMI sound output
# 1: 3.5mm audio jack output
# 2: alsa
disable_1920_1080_60fps = 1
enable_mouse_keyboard = 0

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
	except socket.error as e:
		#connectcounter = connectcounter + 1
		#if connectcounter == 3:
		sock.close()
		sys.exit(1)
	else:
		break

cpuinfo = os.popen('grep Hardware /proc/cpuinfo')
cpustr = cpuinfo.read()
runonpi = 'BCM2835' in cpustr or 'BCM2711' in cpustr
cpuinfo.close()

idrsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
idrsock_address = ('127.0.0.1', 0)
idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
idrsock.bind(idrsock_address)
addr, idrsockport = idrsock.getsockname()

data = sock.recv(2048)
data = data.decode()
print("---M1--->\n" + data)
s_data = '525453502f312e3020323030204f4b0d0a446174653a204d6f6e2c203136204a616e20323032332032333a34303a343020474d540d0a5075626c69633a206f72672e7766612e776664312e302c204745545f504152414d455445522c205345545f504152414d455445520d0a435365713a20310d0a0d0a'
sock.sendall(bytes.fromhex(s_data))

print('sgsdg')

# M2
s_data = '4f5054494f4e53202a20525453502f312e300d0a526571756972653a206f72672e7766612e776664312e300d0a435365713a20310d0a0d0a'
sock.sendall(bytes.fromhex(s_data))

data = sock.recv(2048)
data = data.decode()
print("-------->\n" + data)
m2data = data


# M3
data = sock.recv(2048)
data = data.decode()
print("---M3--->\n" + data)

msg = 'wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\nwfd2_audio_codecs: LPCM 000001ff 00\r\nwfd2_video_formats: 40 01 04 0080 000001ffbdeb 000155557fff 000000000fff 10 0000 001f 11, 01 01 0080 000001ffbdeb 0001555557ff 000000000fff 10 0000 001f 11 00\r\nmicrosoft_video_formats: 0000001fffff\r\nwfd_content_protection: none\r\nwfd_connector_type: 05\r\nwfd_uibc_capability: input_category_list=HIDC;hidc_cap_list=Keyboard/USB, Mouse/USB, MultiTouch/USB, Gesture/USB, RemoteControl/USB, Joystick/USB;port=none\r\nwfd2_video_stream_control: 0f 0f\r\nintel_friendly_name: Tablet\r\nintel_sink_manufacturer_name: Microsoft\r\nintel_sink_model_name: Windows PC\r\nintel_sink_device_URL: none\r\nwfd_idr_request_capability: 1\r\nmicrosoft_latency_management_capability: none\r\nmicrosoft_format_change_capability: supported\r\nmicrosoft_diagnostics_capability: supported\r\nmicrosoft_multiscreen_projection: supported\r\nmicrosoft_audio_mute: supported\r\nmicrosoft_cursor: none 0100 0100 4abf\r\nmicrosoft_rtcp_capability: supported\r\nwfd2_rotation_capability: supported\r\nmicrosoft_max_bitrate: 200000000'



m3resp ='RTSP/1.0 200 OK\r\nCSeq: 2\r\n'+'Content-Type: text/parameters\r\nContent-Length: '+str(len(msg))+'\r\n\r\n'+msg
print("<--------\n" + m3resp)
sock.sendall(m3resp.encode())


# M4
data = sock.recv(2048)
data = data.decode()
print("---M4--->\n" + data)

s_data = 'RTSP/1.0 200 OK\r\nCSeq: 3\r\n\r\n'
print("<--------\n" + s_data)
sock.sendall(s_data.encode())



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
data = sock.recv(2048)
data = data.decode()
print("---M5--->\n" + data)

s_data = 'RTSP/1.0 200 OK\r\nCSeq: 4\r\n\r\n'
print("<--------\n" + s_data)
sock.sendall(s_data.encode())


# M6
m6req ='SETUP rtsp://'+sourceip+'/wfd1.0/streamid=0 RTSP/1.0\r\n'\
+'CSeq: 5\r\n'\
+'Transport: RTP/AVP/UDP;unicast;client_port=1028-1029\r\n\r\n'
print("<---M6---\n" + m6req)
sock.sendall(m6req.encode())

data = sock.recv(2048)
data = data.decode()
print("-------->\n" + data)

paralist=data.split(';')
print(paralist)
serverport=[x for x in paralist if 'server_port=' in x]
print(serverport)
serverport=serverport[-1]
serverport=serverport[12:17]
print(serverport)

paralist=data.split( )
position=paralist.index('Session:')+1
sessionid=paralist[position]





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
		print(sinkip)
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


# M7
m7req ='PLAY rtsp://'+sourceip+'/wfd1.0/streamid=0 RTSP/1.0\r\n'\
+'User-Agent: MSMiracastSink/10.00.19041.2486\r\n'\
+'CSeq: 6\r\n'\
+'Session: '+str(sessionid)+'\r\n\r\n'
print("<---M7---\n" + m7req)
sock.sendall(m7req.encode())

data = sock.recv(2048)
data = data.decode()
print("-------->\n" + data)

print("---- Negotiation successful ----")


while False:
	data = sock.recv(2048)
	data = data.decode()
	print(data)
	if len(data)==0 or 'wfd_trigger_method: TEARDOWN' in data:
		killall(True)
		sleep(1)
		break
	elif 'wfd_video_formats' in data:
		launchplayer(player_select)
	messagelist=data.split('\r\n\r\n')
	print(messagelist)
	singlemessagelist=[x for x in messagelist if ('GET_PARAMETER' in x or 'SET_PARAMETER' in x )]
	print(singlemessagelist)
	for singlemessage in singlemessagelist:
		entrylist=singlemessage.split('\r')
		for entry in entrylist:
			if 'CSeq' in entry:
				cseq = entry

		resp='RTSP/1.0 200 OK\r'+cseq+'\r\n\r\n';#cseq contains \n
		print(resp)
		sock.sendall(resp.encode())



fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
fcntl.fcntl(idrsock, fcntl.F_SETFL, os.O_NONBLOCK)


csnum = 102
watchdog = 0
while True:
	try:
		data = sock.recv(2048)
		data = data.decode()
	except socket.error as e:
		err = e.args[0]
		processrunning = os.popen('ps au').read()
		if player_select == 2 and 'h264.bin' not in processrunning:
			launchplayer(player_select)
		# if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
		# 	try:
		# 		datafromc = idrsock.recv(1000)
		# 		datafromc = datafromc.decode()
		# 	except socket.error as e:
		# 		err = e.args[0]
		# 		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
		# 			processrunning = os.popen('ps au').read()
		# 			if player_select == 2 and 'h264.bin' not in processrunning:
		# 				launchplayer(player_select)						
		# 				sleep(0.01)
		# 			# else:
		# 			# 	watchdog = watchdog + 1
		# 			# 	if watchdog == 70/0.01:
		# 			# 		killall(True)
		# 			# 		sleep(1)
		# 			# 		break
		# 		else:
		# 			sys.exit(1)
		# 	else:
		# 		print(datafromc)
		# 		elemfromc = datafromc.split(' ')				
		# 		if elemfromc[0] == 'recv':
		# 			killall(True)
		# 			sleep(1)
		# 			break


				# else:
				# 	csnum = csnum + 1
				# 	msg = 'wfd_idr_request\r\n'
				# 	idrreq ='SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n'\
				# 	+'Content-Length: '+str(len(msg))+'\r\n'\
				# 	+'Content-Type: text/parameters\r\n'\
				# 	+'CSeq: '+str(csnum)+'\r\n\r\n'\
				# 	+msg
	
				# 	print(idrreq)
				# 	sock.sendall(idrreq.encode())

		# else:
		# 	sys.exit(1)
	else:
		print(data)
		watchdog = 0
		if len(data)==0 or 'wfd_trigger_method: TEARDOWN' in data:
			killall(True)
			sleep(1)
			break
		elif 'wfd_video_formats' in data:
			launchplayer(player_select)
		messagelist=data.split('\r\n\r\n')
		print(messagelist)
		singlemessagelist=[x for x in messagelist if ('GET_PARAMETER' in x or 'SET_PARAMETER' in x )]
		print(singlemessagelist)
		for singlemessage in singlemessagelist:
			entrylist=singlemessage.split('\r')
			for entry in entrylist:
				if 'CSeq' in entry:
					cseq = entry

			resp='RTSP/1.0 200 OK\r'+cseq+'\r\n\r\n';#cseq contains \n
			print(resp)
			sock.sendall(resp.encode())
		
		#uibcstart(sock,data)

idrsock.close()
sock.close()



