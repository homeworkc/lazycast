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
import logging
import socket
import fcntl, os
import errno
import threading
from threading import Thread, Event
import time
from time import sleep
import sys, getopt
import dhcpserver


############### OUTPUT PRINT LEVEL #######################
level_name='info'
debug_to_file='lazy_debug.txt' # only use when level_name='debug'
LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}
sys_logger = logging.getLogger('LazyCast')
################ Dhcp Server Settings ###############
stop_dhcp = Event()
dhcpd = threading.Thread()
SETTINGS = {'NETBOOT_FILE':'',
            'DHCP_INTERFACE':'wlan1',
            'DHCP_SERVER_IP':'192.168.173.1',
            'DHCP_SERVER_PORT':67,
            'DHCP_OFFER_BEGIN':'192.168.173.2',
            'DHCP_OFFER_END':'192.168.173.2',
            'DHCP_SUBNET':'255.255.255.252',
            'DHCP_DNS':'8.8.8.8',
            'DHCP_ROUTER':'192.168.173.1',
            'DHCP_BROADCAST':'',
            'DHCP_FILESERVER':'192.168.173.1',
            'DHCP_WHITELIST':False,
            'LEASES_FILE':'',
            'STATIC_CONFIG':'',
            'USE_IPXE':False,
            'USE_HTTP':False,
            'DHCP_MODE_PROXY':False,
            'MODE_DEBUG': '',
            'MODE_VERBOSE':''} # debug or verbose 'dhcp'
##############################################
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
idrsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def main (argv):

##################### Player Settings #####################
    player_select = 2
    # 0: non-RPi systems. (using vlc)
    # 1: player1 has lower latency.
    # 2: player2 handles still images and sound better.
    sound_output_select = 1
    # 0: HDMI sound output2
    # 1: 3.5mm audio jack output
    # 2: alsa
    disable_1920_1080_60fps = 1
    enable_mouse_keyboard = 0
    
    peeraddress = ''
    interface = ''

############Asing level output information#############

    level = LEVELS.get(level_name, logging.NOTSET)
    sys_logger.setLevel(level)
    if (debug_to_file != "") and (level <= logging.DEBUG):
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s %(message)s')
            logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s %(message)s',filename=debug_to_file,level=level)
    else:
            formatter = logging.Formatter('[%(levelname)s] %(name)s %(message)s')

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    sys_logger.addHandler(handler)

    sys_logger.info('Level output:' + str(level))
    if level <= logging.DEBUG :
            SETTINGS['MODE_DEBUG']='dhcp'
            SETTINGS['MODE_VERBOSE']='dhcp'
    elif   level >= logging.INFO : SETTINGS['MODE_VERBOSE']='dhcp'

#Parameter to create correctly connection
##################### Arguments ####################
    try:
            opts, args = getopt.getopt(argv,"m:p:i:d:h",["ipaddr=","dev="])
            if len(sys.argv) < 3:
                    sys_logger.info( 'd2.py -i <self_ip_address> -m <mask> -d <device> -p <ip_peer_address>')
                    exit()
                    
            for opt, arg in opts:
                if opt == '-h':
                    sys_logger.info( 'd2.py -i <self_ip_address> -m <mask> -d <device> -p <ip_peer_address>')
                    exit()
                elif opt in ("-i", "--ipaddr"):
                    self_ip_address  = arg
                    SETTINGS['DHCP_SERVER_IP']=self_ip_address
                elif opt in ("-d", "--dev"):
                     interface  = arg
                     SETTINGS['DHCP_INTERFACE']=interface 
                elif opt in ("-m", "--mask"):
                     mask  = arg
                     SETTINGS['DHCP_SUBNET']=mask
                elif opt in ("-p", "--ipPeerAddr"):
                    peeraddress  = arg
                    SETTINGS['DHCP_OFFER_BEGIN']=peeraddress
                    SETTINGS['DHCP_OFFER_END']=peeraddress
            
        ##################################################################


            dhcp_server = dhcpserver.DHCPD(
		interface = SETTINGS['DHCP_INTERFACE'],
                ip = SETTINGS['DHCP_SERVER_IP'],
                port = SETTINGS['DHCP_SERVER_PORT'],
                offer_from = SETTINGS['DHCP_OFFER_BEGIN'],
                offer_to = SETTINGS['DHCP_OFFER_END'],
                subnet_mask = SETTINGS['DHCP_SUBNET'],
                router = SETTINGS['DHCP_ROUTER'],
                dns_server = SETTINGS['DHCP_DNS'],
                broadcast = SETTINGS['DHCP_BROADCAST'],
                file_server = SETTINGS['DHCP_FILESERVER'],
                file_name = SETTINGS['NETBOOT_FILE'],
                use_ipxe = SETTINGS['USE_IPXE'],
                use_http = SETTINGS['USE_HTTP'],
                mode_proxy = SETTINGS['DHCP_MODE_PROXY'],
                mode_debug = do_debug('dhcp'),
                mode_verbose = do_verbose('dhcp'),
                whitelist = SETTINGS['DHCP_WHITELIST'],
                logger = sys_logger,
                saveleases = SETTINGS['LEASES_FILE'])
            dhcpd = threading.Thread(target = run_dhcp, args=(dhcp_server,))
            dhcpd.start()      

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (peeraddress , 7236)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, 25, interface +'\0')
            sock.settimeout(3)

            idrsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            idrsock_address = ('127.0.0.1', 0)
            idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            idrsock.bind(idrsock_address)
            addr, idrsockport = idrsock.getsockname()
            
            isOpen = False
            sys_logger.info("Waiting to : " + str(peeraddress) + " in " + str(interface) + " " +
                str(self_ip_address) + " / " + str(mask))

            while  isOpen == False:
                try:
                    sock.connect(server_address)
                    isOpen = True
                except KeyboardInterrupt:
                    sys_logger.info(' Exit KeyboardInterrupt')
                    close_me()
                except:   
                    sleep (0.4)

            sys_logger.info('-----Peer connected-----')
            sock.settimeout(socket.getdefaulttimeout())

            data = (sock.recv(1000))
            sys_logger.debug( "---M1--->\n" + str(data) )
            s_data = 'RTSP/1.0 200 OK\r\nCSeq: 1\r\n\Public: org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER\r\n\r\n'
            sys_logger.debug( "<--------\n" + s_data )
            sock.sendall(s_data)


            # M2
            s_data = 'OPTIONS * RTSP/1.0\r\nCSeq: 100\r\nRequire: org.wfa.wfd1.0\r\n\r\n'
            sys_logger.debug( "<---M2---\n" + s_data )
            sock.sendall(s_data)

            data = (sock.recv(1000))
            sys_logger.debug( "-------->\n" + data )


            # M3
            data=(sock.recv(1000))
            sys_logger.debug( "---M3--->\n" + data)

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
            sys_logger.debug( "<--------\n" + m3resp)
            sock.sendall(m3resp)


            # M4
            data=(sock.recv(1000))
            sys_logger.debug( "---M4--->\n" + data)

            s_data = 'RTSP/1.0 200 OK\r\nCSeq: 3\r\n\r\n'
            sys_logger.debug( "<--------\n" + s_data)
            sock.sendall(s_data)

            uibcstart(sock,data,enable_mouse_keyboard)

            # M5
            data=(sock.recv(1000))
            sys_logger.debug( "---M5--->\n" + str(data))

            s_data = 'RTSP/1.0 200 OK\r\nCSeq: 4\r\n\r\n'
            sys_logger.debug( "<--------\n" + s_data )
            sock.sendall(s_data)


            # M6
            m6req ='SETUP rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n'\
            +'CSeq: 101\r\n'\
            +'Transport: RTP/AVP/UDP;unicast;client_port=1028\r\n\r\n'
            sys_logger.debug( "<---M6---\n" + m6req)
            sock.sendall(m6req)

            data=(sock.recv(1000))
            sys_logger.debug( "-------->\n" + data )

            paralist=data.split(';')
            sys_logger.debug(paralist)
            serverport=[x for x in paralist if 'server_port=' in x]
            sys_logger.debug( serverport)
            
            serverport=serverport[12:17]
            sys_logger.debug( serverport)

            paralist=data.split( )
            position=paralist.index('Session:')+1
            sessionid=paralist[position]


            # M7
            m7req ='PLAY rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n'\
            +'CSeq: 102\r\n'\
            +'Session: '+str(sessionid)+'\r\n\r\n'
            sys_logger.debug( "<---M7---\n" + m7req)
            sock.sendall(m7req)

            data=(sock.recv(1000))
            sys_logger.debug( "-------->\n" + str(data))

            sys_logger.info("----Negotiation successful ----")


            if (os.uname()[-1][:4] != "armv"):
                player_select = 0
            sys_logger.debug("----lauchplayer ----")
            launchplayer(player_select,idrsockport,sound_output_select)

            fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
            fcntl.fcntl(idrsock, fcntl.F_SETFL, os.O_NONBLOCK)

            csnum = 102
            watchdog = 0
            while True:
                try:
                    data = (sock.recv(2096))
                except socket.error, e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        try:
                            datafromc = idrsock.recv(2096)
                        except socket.error, e:
                            err = e.args[0]
                            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                                sleep(0.01)
                                watchdog = watchdog + 1
                                if watchdog == 70/0.01:
                                    sys_logger.error( "ERROR receiver data watchdog reach the max value (watchdog)="+ (watchdog))
                                    break
                            else:
                                sys_logger.error( "ERROR distint errno.EAGAIN errno.EWOULDBLOCK, (watchdog)="+ (watchdog))
                                break
                        else:
                            sys_logger.debug( 'ags8jgajdgkajsdlfj;asdkfasdf'+datafromc)
                            elemfromc = datafromc.split(' ')                
                            if elemfromc[0] == 'recv':
                                sys_logger.error( "ERROR  data receiver = recv")
                                break
                            else:
                                csnum = csnum + 1
                                msg = 'wfd-idr-request\r\n'
                                idrreq ='SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n'\
                                +'Content-Length: '+str(len(msg))+'\r\n'\
                                +'Content-Type: text/parameters\r\n'\
                                +'CSeq: '+str(csnum)+'\r\n\r\n'\
                                +msg
                
                                sys_logger.debug( idrreq)
                                sock.sendall(idrreq)

                    else:
                        break
                else:                    
                    sys_logger.debug( "Data:"+ str(data) )
                    watchdog = 0
                    #if len(data)==0 or 'wfd_trigger_method: TEARDOWN' in data:
                    if 'wfd_trigger_method: TEARDOWN' in data:
                        sys_logger.error( "ERROR data len 0 or TEARDOWN")
                        break
                    elif 'wfd_video_formats' in data:
                       
                       launchplayer(player_select,idrsockport,sound_output_select)        
                    messagelist=data.split('\r\n\r\n')
                    sys_logger.debug("Message:" + str(messagelist))
                    singlemessagelist=[x for x in messagelist if ('GET_PARAMETER' in x or 'SET_PARAMETER' in x )]
                    sys_logger.debug("Single message:" + str(singlemessagelist))
                    for singlemessage in singlemessagelist:
                        entrylist=singlemessage.split('\r')
                        for entry in entrylist:
                            if 'CSeq' in entry:
                                cseq = entry

                        resp='RTSP/1.0 200 OK\r'+cseq+'\r\n\r\n';#cseq contains \n
                        sys_logger.debug("Response:" +str (resp))
                        sock.sendall(resp)
                    
                    uibcstart(sock,data,enable_mouse_keyboard)

            sys_logger.info( "Exit of main loop, Reason:" + str(e)) 
            close_me()

    except getopt.GetoptError:
            sys_logger.info( 'd2.py -i <self_ip_address> -m <mask> -d <device> -p <ip_peer_address>')
            close_me()
 
    except KeyboardInterrupt:
            sys_logger.info(' Exit KeyboardInterrupt')
            close_me()

    except socket.error, e:
            sys_logger.error( ' ERROR socket.error')
            close_me()

    except Exception,e: 
            sys_logger.error("Excepcion:"+ str(e))
            close_me()

def close_me():
    sys_logger.info( ' Exit')
    os.system('pkill control.bin')
    os.system('pkill controlhidc.bin')
    os.system('pkill vlc')
    os.system('pkill player.bin')
    os.system('pkill h264.bin')
    stop_dhcp.set()
    sys_logger.info( "Stoping DHCP SERVER:" + str (stop_dhcp.is_set()))
    while dhcpd.isAlive():
        time.sleep (0.5)
    if sock:
        sock.close()
    if idrsock:
        idrsock.close()
    sys.exit(1)


def launchplayer(player_select, idrsockport, sound_output_select):
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

def uibcstart(sock, data, enable_mouse_keyboard):
    sys_logger.debug("Uibcstart data:" + str(data))
    messagelist=data.split('\r\n\r\n')
    for entry in messagelist:
        if 'wfd_uibc_capability:' in entry:
            entrylist = entry.split(';')
            uibcport = entrylist[-1]
            uibcport = uibcport.split('\r')
            uibcport = uibcport[0]
            uibcport = uibcport.split('=')
            uibcport = uibcport[1]
            sys_logger.info( 'uibcport:'+uibcport+"\n")
            if 'none' not in uibcport and enable_mouse_keyboard == 1:
                os.system('pkill control.bin')
                os.system('pkill controlhidc.bin')
                if('hidc_cap_list=none' not in entry):
                    os.system('./control/controlhidc.bin '+ uibcport + ' &')
                elif('generic_cap_list=none' not in entry):
                    os.system('./control/control.bin '+ uibcport + ' &')


def do_debug(service):
    return ((service in SETTINGS['MODE_DEBUG'].lower()
            or 'all' in SETTINGS['MODE_DEBUG'].lower())
            and '-{0}'.format(service) not in SETTINGS['MODE_DEBUG'].lower())

def do_verbose(service):
    return ((service in SETTINGS['MODE_VERBOSE'].lower()
            or 'all' in SETTINGS['MODE_VERBOSE'].lower())
            and '-{0}'.format(service) not in SETTINGS['MODE_VERBOSE'].lower())	

def run_dhcp(dhcp_server): 
    ref=0
    while True: 
        dhcp_server.listen()
        num_lease=dhcp_server.num_leased()
        if num_lease!=ref:
            ref=num_lease
            sys_logger.info("Assigned ip address:" + str(num_lease))
        if stop_dhcp.is_set(): 
            break


if __name__=="__main__":
    main (sys.argv[1:])




