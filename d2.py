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




tohid = [0, 41, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 45, 46, 42, 43, 20, 26, 8, 21, 23, 28, 24, 12, 18, 19, 47, 48, 40, 0, 4, 22, 7, 9, 10, 11, 13, 14, 15, 51, 52, 53, 0, 49, 29, 27, 6, 25, 5, 17, 16, 54, 55, 56, 0, 85, 0, 44, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 83, 71, 95, 96, 97, 86, 92, 93, 94, 87, 89, 90, 91, 98, 99, 0, 0, 0, 68, 69, 0, 0, 0, 0, 0, 0, 0, 88, 0, 84, 70, 0, 0, 74, 82, 75, 80, 79, 77, 81, 78, 73, 76, 0, 127, 129, 128, 0, 0, 0, 72, 
0,0,0,0,0,0,0,0x65]

def hidcprocessing(hidcsock):
	print('hidcprocessing')
	mousemask = 0
	keyboardmask = 0
	while(1):
		for key,mask in selector.select():
			device = key.fileobj
			for event in device.read():

				if event.type == 0:
					continue

				if event.type ==  ecodes.EV_KEY:
					
					if(event.code<272):
						keyin = event.code

						keyout = 0
						if (keyin == 29): #left ctrl
							if(event.value == 0):
								keyboardmask &= ~1
							else:
								keyboardmask |= 1
						elif (keyin == 42): #left shift
							if(event.value == 0):
								keyboardmask &= ~(1<<1) #shift
							else:
								keyboardmask |= (1<<1)
						elif (keyin == 56): #left alt
							if(event.value == 0):
								keyboardmask &= ~(1<<2)
							else:
								keyboardmask |= (1<<2)
						elif (keyin == 125): #leftmeta
							if(event.value == 0):
								keyboardmask &= ~(1<<3) #windows
							else:
								keyboardmask |= (1<<3)
						elif (keyin == 97):#right ctrl
							if(event.value == 0):
								keyboardmask &= ~(1<<4)
							else:
								keyboardmask |= (1<<4)
						elif (keyin == 54):#right shift
							if(event.value == 0):
								keyboardmask &= ~(1<<5)
							else:
								keyboardmask |= (1<<5)
						elif (keyin == 100):#right alt
							if(event.value == 0):
								keyboardmask &= ~(1<<6)
							else:
								keyboardmask |= (1<<6)
						elif (keyin == 0x7e): #rightmeta
							if(event.value == 0):
								keyboardmask &= ~(1<<7) #windows
							else:
								keyboardmask |= (1<<7)
						else:
							if(event.value != 0):
								keyout = tohid[keyin]
								
						m7 = '00010012010000000929'+'{:02x}'.format(keyboardmask)+'00'+'{:02x}'.format(keyout)+'0000000000'
						hidcsock.send(bytes.fromhex(m7))


					elif(event.code == 272): # left
						if(event.value == 1):
							mousemask |= 1
						else:
							mousemask &= ~1
						m7 = '00010010010100000628'+'{:02x}'.format(mousemask & 0xFF)+'0000000000'
						hidcsock.send(bytes.fromhex(m7))
					elif(event.code == 273): 
						if(event.value == 1):
							mousemask |= 2
						else:
							mousemask &= ~2
						m7 = '00010010010100000628'+'{:02x}'.format(mousemask & 0xFF)+'0000000000'
						hidcsock.send(bytes.fromhex(m7))
					elif(event.code == 274): 
						if(event.value == 1):
							mousemask |= 4
						else:
							mousemask &= ~4
						m7 = '00010010010100000628'+'{:02x}'.format(mousemask & 0xFF)+'0000000000'
						hidcsock.send(bytes.fromhex(m7))

				elif event.type == ecodes.EV_REL:
					if(event.code == 0): #x
						m7 = '00010010010100000628'+'{:02x}'.format(mousemask & 0xFF)+'{:02x}'.format(event.value & 0xFF)+'00000000'
						hidcsock.send(bytes.fromhex(m7))
					elif(event.code == 1): #y
						m7 = '00010010010100000628'+'{:02x}'.format(mousemask & 0xFF)+'00'+'{:02x}'.format(event.value & 0xFF)+'000000'
						hidcsock.send(bytes.fromhex(m7))
					elif(event.code == 8): # wheel
						if(event.value<0):
							m7 = '00010010010100000628'+'{:02x}'.format(mousemask & 0xFF)+'0000FF0000'
						else:
							m7 = '00010010010100000628'+'{:02x}'.format(mousemask & 0xFF)+'0000010000'
						hidcsock.send(bytes.fromhex(m7))





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
s_data = 'RTSP/1.0 200 OK\r\nCSeq: 1\r\nPublic: org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER\r\n\r\n'
print("<--------\n" + s_data)
sock.sendall(s_data.encode())


# M2
s_data = 'OPTIONS * RTSP/1.0\r\nCSeq: 1\r\nRequire: org.wfa.wfd1.0\r\n\r\n'
print("<---M2---\n" + s_data)
sock.sendall(s_data.encode())

data = sock.recv(2048)
data = data.decode()
print("-------->\n" + data)
m2data = data


# M3
data = sock.recv(2048)
data = data.decode()
print("---M3--->\n" + data)

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


if runonpi:
	os.system('tvservice -d edid.txt')
	os.system('pkill lxpanel')

edidlen = 0
if os.path.exists('edid.txt') and True:
	edidfile = open('edid.txt','rb')
	edidbytes = edidfile.read()
	edidfile.close()
	edidlen = len(edidbytes)

if 'wfd_display_edid' in data and edidlen != 0:
	msg = msg + 'wfd_display_edid: ' + '{:04X}'.format(int(edidlen/256 + 1)) + ' ' + str(edidbytes.hex())+'\r\n'

# if 'microsoft_latency_management_capability' in data:
# 	msg = msg + 'microsoft-latency-management-capability: supported\r\n'
# if 'microsoft_format_change_capability' in data:
# 	msg = msg + 'microsoft_format_change_capability: supported\r\n'

if 'intel_friendly_name' in data:
	msg = msg + 'intel_friendly_name: raspberrypi\r\n'
if 'intel_sink_manufacturer_name' in data:
	msg = msg + 'intel_sink_manufacturer_name: lazycast\r\n'
if 'intel_sink_model_name' in data:
	msg = msg + 'intel_sink_model_name: lazycast\r\n'
if 'intel_sink_version' in data:
	msg = msg + 'intel_sink_version: 20.4.26\r\n'
if 'intel_sink_device_URL' in data:
	msg = msg + 'intel_sink_device_URL: https://github.com/homeworkc/lazycast\r\n'




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

usehidc = False
messagelist=data.split('\r\n\r\n')
for entry in messagelist:
	if 'wfd_uibc_capability:' in entry:
		entrylist = entry.split(';')
		uibcport = entrylist[-1]
		uibcport = uibcport.split('\r')
		uibcport = uibcport[0]
		uibcport = uibcport.split('=')
		uibcport = uibcport[1]
		print('uibcport:'+uibcport+"\n")
		if 'none' not in uibcport and enable_mouse_keyboard == 1:
			usehidc = True



if usehidc:
	from evdev import InputDevice, categorize, ecodes
	import evdev
	from selectors import DefaultSelector, EVENT_READ

	hidcsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	hidcsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	hidcsock.connect((sourceip,int(uibcport)))


	m1 = '1001003e2ab6010101003305010902a10185280901a1000509190129081500250195087501810205010930093109380a38021581257f750895048106c0c0'
	m2 = '1001004c3ce2010001004105010906a1018529050719e029e71500250175019508810295017508810395057501050819012905910295017503910395067508150025650507190029658100c0'
	m3 = '100100243ce20107010019050c0901a101852a19002aff00150026ff00950175108100c0'
	m4 = '1001027a3ce2010301026f050d0904a1018513050d095495017508150025638102550c66011047ffff000027ffff00007510950109568102050d0922a102150025013500450055006500750195010942810209478102950481030600ff09109501750281027508050d095126630081027510550e651127ff7f00004640060948810209498102050109308102468403050109318102050d651447a08c000027a08c0000093f8102c0050d0922a102150025013500450055006500750195010942810209478102950481030600ff09109501750281027508050d095126630081027510550e651127ff7f00004640060948810209498102050109308102468403050109318102050d651447a08c000027a08c0000093f8102c0050d0922a102150025013500450055006500750195010942810209478102950481030600ff09109501750281027508050d095126630081027510550e651127ff7f00004640060948810209498102050109308102468403050109318102050d651447a08c000027a08c0000093f8102c0050d0922a102150025013500450055006500750195010942810209478102950481030600ff09109501750281027508050d095126630081027510550e651127ff7f00004640060948810209498102050109308102468403050109318102050d651447a08c000027a08c0000093f8102c0050d0922a102150025013500450055006500750195010942810209478102950481030600ff09109501750281027508050d095126630081027510550e651127ff7f00004640060948810209498102050109308102468403050109318102050d651447a08c000027a08c0000093f8102c0050d85120955950175101500266400b102c0'
	m5 = '1001000e3ce20103000003120a00'
	m6 = '100100d0422801060100c4050d0902a1018514050d0920a10009420944093c094509321500250175019505810295038103050127ff7f000075109501550e6533093035004640068142093146840381426500050d093081020600ff09118102091281027520050609228102c0c0050d0902a1018515050d0920a10009420944093c094509321500250175019505810295038103050127ff7f000075109501550e6533093035004640068142093146840381426500050d093081020600ff09118102091281027520050609228102c0c000'


	hidcsock.send(bytes.fromhex(m1))
	sleep(0.01)
	hidcsock.send(bytes.fromhex(m2))
	sleep(0.01)
	hidcsock.send(bytes.fromhex(m3))
	sleep(0.01)
	hidcsock.send(bytes.fromhex(m4))
	sleep(0.01)
	hidcsock.send(bytes.fromhex(m5))
	sleep(0.01)
	hidcsock.send(bytes.fromhex(m6))
	sleep(0.01)
	selector = DefaultSelector()


	phys = []
	for path in evdev.list_devices():
		inputdev = InputDevice(path)
		selector.register(inputdev, EVENT_READ)
		if inputdev.phys not in phys:
			inputdev.grab()
			phys.append(inputdev.phys)

	t1 = threading.Thread(target=hidcprocessing, args=(hidcsock,))
	t1.start()







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
+'Transport: RTP/AVP/UDP;unicast;client_port=1028\r\n\r\n'
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
+'CSeq: 6\r\n'\
+'Session: '+str(sessionid)+'\r\n\r\n'
print("<---M7---\n" + m7req)
sock.sendall(m7req.encode())

data = sock.recv(2048)
data = data.decode()
print("-------->\n" + data)

print("---- Negotiation successful ----")

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
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			try:
				datafromc = idrsock.recv(1000)
				datafromc = datafromc.decode()
			except socket.error as e:
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
				print(datafromc)
				elemfromc = datafromc.split(' ')				
				if elemfromc[0] == 'recv':
					killall(True)
					sleep(1)
					break
				else:
					csnum = csnum + 1
					msg = 'wfd_idr_request\r\n'
					idrreq ='SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n'\
					+'Content-Length: '+str(len(msg))+'\r\n'\
					+'Content-Type: text/parameters\r\n'\
					+'CSeq: '+str(csnum)+'\r\n\r\n'\
					+msg
	
					print(idrreq)
					sock.sendall(idrreq.encode())

		else:
			sys.exit(1)
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
		

idrsock.close()
sock.close()


if runonpi:
	os.system('nohup lxpanel --profile LXDE-pi &')

if usehidc:
	hidcsock.close()
	for path in evdev.list_devices():
		inputdev = InputDevice(path)
		try:
			inputdev.ungrab()
		except IOError:
			print('already ungrabbed')
		