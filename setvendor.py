#!/usr/bin/env python2


import os
import socket


hostname = socket.gethostname()

# hostname = 'Dummy1-Kabylake'
hostnamehex = hostname.encode('hex')

hostnamemessage = '2002'+'{:04X}'.format(len(hostname))+hostnamehex
# print hostnamemessage

iphex = '192.168.200.1'.encode('hex')

ipmessage = '2005'+'{:04X}'.format(len(iphex)/2)+iphex



#capandhostmessage = '0001372001000105' + hostnamemessage + ipmessage
capandhostmessage = '0001372001000107' + hostnamemessage


wscmessage = '0050F204'+'1049'+'{:04X}'.format(len(capandhostmessage)/2) + capandhostmessage
# print wscmessage
message = 'DD' + '{:02X}'.format(len(wscmessage)/2) + wscmessage
print message

os.system('sudo wpa_cli VENDOR_ELEM_ADD 1 '+message)
os.system('sudo wpa_cli VENDOR_ELEM_ADD 2 '+message)
os.system('sudo wpa_cli VENDOR_ELEM_ADD 3 '+message)