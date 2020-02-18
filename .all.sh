#!/bin/bash +x
#################################################################################
# Run script for lazycast
# Licensed under GNU General Public License v3.0 GPL-3 (in short)
#
#   You may copy, distribute and modify the software as long as you track
#   changes/dates in source files. Any modifications to our software
#   including (via compiler) GPL-licensed code must also be made available
#   under the GPL along with build & install instructions.
#
#################################################################################
# define options
pin="69696969"
ip_neighbor="192.168.173.2"
ip_interface="192.168.173.1"
mask="255.255.255.252"
select_interface="wlan0"
################################################
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
#Main

#interface select
#
wpa_cli interface $select_interface
wpa_status="$(wpa_cli status)"
mac_addr_interface="$(echo "${wpa_status}"  | grep p2p_device_address | cut -d"=" -f2)"

#wpa status
if [[ "${wpa_status}" !=  *"wpa_state=COMPLETED"* ]]; then
		echo "configuring WPA_supplicant"
		wpa_cli set p2p_go_ht40 1
		wpa_cli p2p_find type=progessive
		wpa_cli set device_name DIRECT-"$(uname -n)"
		wpa_cli set device_type 7-0050F204-1
		wpa_cli set p2p_go_ht40 1
		wpa_cli wfd_subelem_set 0 000600111c44012c
		wpa_cli wfd_subelem_set 1 0006000000000000
		wpa_cli wfd_subelem_set 6 000700000000000000


		# check if the interface was used to P2P connection before
		perentry="$(wpa_cli list_networks | grep "\[DISABLED\]\[P2P-PERSISTENT\]" | tail -1)"
		echo "${perentry}"
		if [ `echo "${perentry}" | grep -c "P2P-PERSISTENT"`  -gt 0 ] 
		then
                	networkid=${perentry%%D*}
                	perstr="=${networkid}"
		else
                	perstr=""
		fi

		wpa_cli p2p_group_add persistent$perstr


fi


interface="$(wpa_cli status | grep "Selected interface" | cut -d"'" -f2)" 

#check if the interface exist
if [[  "$(iw dev $interface info 2>&1)" ==  *"No such device"*  ]]; then
		wpa_cli p2p_group_add persistent$perstr
		sleep 2
		if [[ "$(iw dev $interface info 2>&1)" ==  *"No such device"* ]]; then
				echo Device error:$interface
				break
     else
		    if [[ "$(iw dev $interface info 2>&1 | grep type)" ==  *"P2P"* ]]; then
             echo "Interface UP:"$interface " in P2P mode"

				else
			    	 echo "Interface UP:"$interface "but not in P2P mode"
				fi
		fi
fi
echo "WPA config in P2P mode"

#config ip address		
ifconfig $interface $ip_interface
ifconfig $interface netmask $mask

echo "The display is ready"
echo "Your device is called: DIRECT-"$(uname -n)""
echo "PIN-->"     
sudo wpa_cli -i$interface wps_pin any $pin
echo "<--PIN

echo "Waiting connection"
./d2.py -i$ip_interface -m$mask -p$ip_neighbor   -d$interface

#clear p2p connection and arp entry
echo "Connection Finished"
wpa_cli p2p_flush
ip neigh flush  $ip_neighbor

