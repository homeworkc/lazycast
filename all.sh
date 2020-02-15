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
pin=69696969
ip_neighbor="192.168.173.2"
ip_interface="192.168.173.1"
mask="255.255.255.252"
interface="wlan0"
################################################
#Main LOOP
while true; do
		#interface select
		#
                wpa_cli interface $interface
                #ain="$(sudo wpa_cli $interface)"
                ain="$(sudo wpa_cli interface)"
                echo "${ain}"
		interface=$(echo "${ain}" | grep "wl" | grep -v "interface")

		#interfaces type is now configured to  P2P?
		type="$(iw dev "$interface" info | grep type)"

		if [ `echo "${type}" | grep -c "P2P"` -gt 0 ] 
		then
			echo "already on"

		else
		# if not
		#config wpa_supplicant to P2P connection 
			sudo wpa_cli set p2p_go_ht40 1
			sudo wpa_cli p2p_find type=progessive
			sudo wpa_cli set device_name DIRECT-"$(uname -n)"
			sudo wpa_cli set device_type 7-0050F204-1
			sudo wpa_cli set p2p_go_ht40 1
			sudo wpa_cli wfd_subelem_set 0 000600111c44012c
			sudo wpa_cli wfd_subelem_set 1 0006000000000000
			sudo wpa_cli wfd_subelem_set 6 000700000000000000
			
			perentry="$(wpa_cli list_networks | grep "\[DISABLED\]\[P2P-PERSISTENT\]" | tail -1)"
			echo "${perentry}"

		# check if the interface was used to P2P connection before
		# and select de ID 
			if [ `echo "${perentry}" | grep -c "P2P-PERSISTENT"`  -gt 0 ] 
			then
				networkid=${perentry%%D*}
				perstr="=${networkid}"
			else
				perstr=""
			fi
			

		#check if  iw dev can put in p2p-go
			echo "${perstr}"
			interface=$(echo "${ain}" | grep "wl" | grep -v "interface")
			type="$(iw dev "$interface" info | grep type)"
			

			while [ `echo "${type}" | grep -c "P2P"`  -lt 1 ] 
			do
				while [ `echo "${type}" | grep -c "P2P"`  -lt 1 ]
					do
					sudo wpa_cli p2p_group_add persistent$perstr 
					#sudo wpa_cli p2p_group_add persistent$perstr ht40
					sleep 2
					ain="$(sudo wpa_cli interface)"
					echo "$ain"
						interface=$(echo "${ain}" | grep "wl" | grep -v "interface")
						type="$(iw dev "$interface" info | grep type)"

				done
				ain="$(sudo wpa_cli interface)"
						echo "$ain"
					interface=$(echo "${ain}" | grep "wl" | grep -v "interface")
					type="$(iw dev "$interface" info | grep type)"
			done

		fi

		p2pinterface=$(echo "${ain}" | grep "wl" | grep -v "interface")
		echo $p2pinterface

		sudo ifconfig $p2pinterface $ip_interface
		sudo ifconfig $p2pinterface netmask $mask

		echo "The display is ready"
		echo "Your device is called: DIRECT-"$(uname -n)""
		echo "PIN-->"     
		sudo wpa_cli -i$p2pinterface wps_pin any $pin
		echo "<--PIN"

		echo "Waiting connection"
		./d2.py -i$ip_interface -m$mask -p$ip_neighbor   -d$p2pinterface

		#clear p2p connection and arp entry
		echo "Reconnecting"
		sudo wpa_cli p2p_flush
		sudo ip neigh flush  $ip_neighbor
done
