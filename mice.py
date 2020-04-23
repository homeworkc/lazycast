#!/usr/bin/env python2
"""
	This software is part of lazycast, a simple wireless display receiver for Raspberry Pi
	Copyright (C) 2020 Hsun-Wei Cho
	Modified from the p2p_group_add example of wpa_supplicant
	# Tests p2p_group_add
	######### MAY NEED TO RUN AS SUDO #############
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
import dbus
import sys, os
import time
import gobject
import threading
import socket
from dbus.mainloop.glib import DBusGMainLoop
from time import sleep
from threading import Event
import uuid

event = Event()

def groupStarted(properties):

	print "groupStarted: " + str(properties)
	g_obj = dbus.SystemBus().get_object('fi.w1.wpa_supplicant1',properties['group_object'])
	res = g_obj.GetAll('fi.w1.wpa_supplicant1.Group', dbus_interface=dbus.PROPERTIES_IFACE, byte_arrays=True)
	print "Group properties: " + str(res)


	hostname = socket.gethostname()
	hostnamehex = hostname.encode('hex')

	hostnamemessage = '2002'+'{:04X}'.format(len(hostname))+hostnamehex
	capandhostmessage = '0001372001000105' + hostnamemessage

	innerarray = []
	for c in capandhostmessage.decode('hex'):
		innerarray.append(dbus.Byte(c))

	g_obj.Set('fi.w1.wpa_supplicant1.Group', 'WPSVendorExtensions',  
	dbus.Array([dbus.Array(innerarray, signature=dbus.Signature('ay'))], signature=dbus.Signature('ay')),dbus_interface=dbus.PROPERTIES_IFACE)

	g_obj = dbus.SystemBus().get_object('fi.w1.wpa_supplicant1',properties['group_object'])
	res = g_obj.GetAll('fi.w1.wpa_supplicant1.Group', dbus_interface=dbus.PROPERTIES_IFACE, byte_arrays=True)
	print "Group properties: " + str(res)

	event.set()
	




def WpsFailure(status, etc):
	print("WPS Authentication Failure".format(status))
	print(etc)
	os._exit(0)

class P2P_Group_Add (threading.Thread):
	# Needed Variables
	global bus
	global wpas_object
	global interface_object
	global interfacep2pdevice
	global interface_name
	global wpas
	global wpas_dbus_interface
	global path

	# Dbus Paths
	global wpas_dbus_opath
	global wpas_dbus_interfaces_opath
	global wpas_dbus_interfaces_interface
	global wpas_dbus_interfaces_p2pdevice


	# Constructor
	def __init__(self,interface_name,wpas_dbus_interface):
		# Initializes variables and threads
		self.interface_name = interface_name
		self.wpas_dbus_interface = wpas_dbus_interface
		

		# Initializes thread and daemon allows for ctrl-c kill
		threading.Thread.__init__(self)
		self.daemon = True

		# Generating interface/object paths
		self.wpas_dbus_opath = "/" + self.wpas_dbus_interface.replace(".","/")
		self.wpas_wpas_dbus_interfaces_opath = self.wpas_dbus_opath + "/Interfaces"
		self.wpas_dbus_interfaces_interface = self.wpas_dbus_interface + ".Interface"
		self.wpas_dbus_interfaces_p2pdevice = self.wpas_dbus_interfaces_interface + ".P2PDevice"

		# Getting interfaces and objects
		DBusGMainLoop(set_as_default=True)
		self.bus = dbus.SystemBus()
		self.wpas_object = self.bus.get_object(self.wpas_dbus_interface, self.wpas_dbus_opath)
		self.wpas = dbus.Interface(self.wpas_object, self.wpas_dbus_interface)

		# Try to see if supplicant knows about interface
		# If not, throw an exception
		try:
			self.path = self.wpas.GetInterface(self.interface_name)
		except dbus.DBusException as exc:
			error = 'Error:\n  Interface ' + self.interface_name + ' was not found'
			print(error)
			usage()
			os._exit(0)

		self.interface_object = self.bus.get_object(self.wpas_dbus_interface, self.path)
		self.interfacep2pdevice = dbus.Interface(self.interface_object, self.wpas_dbus_interfaces_p2pdevice)

		self.bus.add_signal_receiver(groupStarted, dbus_interface=self.wpas_dbus_interfaces_p2pdevice,
			signal_name="GroupStarted")
		self.bus.add_signal_receiver(WpsFailure, dbus_interface=self.wpas_dbus_interfaces_p2pdevice,
			signal_name="WpsFailed")


	def setarguments(self):

		hostname = socket.gethostname()


		props = self.interface_object.GetAll(self.wpas_dbus_interfaces_p2pdevice,dbus_interface=dbus.PROPERTIES_IFACE)
		print(props)
		print ''	

		dbus.Interface(self.interface_object, dbus_interface=dbus.PROPERTIES_IFACE).Set(self.wpas_dbus_interfaces_p2pdevice, 'P2PDeviceConfig',dbus.Dictionary({ 'DeviceName' : hostname},signature='sv'))

		dbus.Interface(self.interface_object, dbus_interface=dbus.PROPERTIES_IFACE).Set(self.wpas_dbus_interfaces_p2pdevice, 'P2PDeviceConfig',dbus.Dictionary({dbus.String(u'PrimaryDeviceType'): dbus.Array([dbus.Byte(0), dbus.Byte(7), dbus.Byte(0), dbus.Byte(80), dbus.Byte(242), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0)])},signature='sv'))

		dbus.Interface(self.wpas_object, dbus_interface=dbus.PROPERTIES_IFACE).Set('fi.w1.wpa_supplicant1', dbus.String(u'WFDIEs'), dbus.Array([dbus.Byte(0), dbus.Byte(0), dbus.Byte(6), dbus.Byte(1), dbus.Byte(81), dbus.Byte(2), dbus.Byte(42), dbus.Byte(1), dbus.Byte(44), dbus.Byte(1), dbus.Byte(0), dbus.Byte(6), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(6), dbus.Byte(0), dbus.Byte(7), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0)], signature=dbus.Signature('y'), variant_level=1))

		props = self.wpas_object.GetAll('fi.w1.wpa_supplicant1',dbus_interface=dbus.PROPERTIES_IFACE)
		print(props)
		print ''	


	def run(self):

		groupadddict = {'persistent':False}
		try:
			self.interfacep2pdevice.GroupAdd(groupadddict)
		except:
			print("Error:\n  Could not preform group add")
			os._exit(0)

		gobject.MainLoop().get_context().iteration(True)
		gobject.threads_init()
		gobject.MainLoop().run()



		



if __name__ == "__main__":

	try:
		p2p_group_add_test = P2P_Group_Add('wlan0','fi.w1.wpa_supplicant1')
	except:
		print("Error:\n  Invalid Arguements")

	p2p_group_add_test.setarguments()
	p2p_group_add_test.start()


	event.wait()

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

	print uuidstr

	hostname = socket.gethostname()
	dnsstr = 'avahi-publish-service '+hostname+' _display._tcp 7250 container_id={'+uuidstr+'}'
	print dnsstr
	os.system(dnsstr+' &')
	execfile('project.py')

	# print("Error:\n  Group formation timed out")
	# os._exit(0)
