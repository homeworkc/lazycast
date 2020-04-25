#!/bin/bash
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
managefrequency=1
while :
do
	p2pdevinterface=$(sudo wpa_cli interface | grep -E "p2p-dev" | tail -1)
	wlaninterface=$(echo $p2pdevinterface | cut -c1-8 --complement)
	echo $p2pdevinterface
	echo $wlaninterface
	ain="$(sudo wpa_cli interface)"
	echo "${ain}"
	if [ `echo "${ain}" | grep -c "p2p-wl"` -gt 0 ] 
	then
		echo "already on"

	else
		sudo wpa_cli -i$p2pdevinterface p2p_find type=progessive
		sudo wpa_cli -i$p2pdevinterface set device_name "$(uname -n)"
		sudo wpa_cli -i$p2pdevinterface set device_type 7-0050F204-1
		sudo wpa_cli -i$p2pdevinterface set p2p_go_ht40 1
		sudo wpa_cli -i$p2pdevinterface wfd_subelem_set 0 000600111c44012c
		sudo wpa_cli -i$p2pdevinterface wfd_subelem_set 1 0006000000000000
		sudo wpa_cli -i$p2pdevinterface wfd_subelem_set 6 000700000000000000
		perentry="$(sudo wpa_cli -i$p2pdevinterface list_networks | grep "\[DISABLED\]\[P2P-PERSISTENT\]" | tail -1)"
		echo "${perentry}"
		if [ `echo "${perentry}" | grep -c "P2P-PERSISTENT"`  -gt 0 ] 
		then
			networkid=${perentry%%D*}
			perstr="=${networkid}"
		else
			perstr=""
		fi
		echo "${perstr}"
		echo "${p2pdevinterface}"
		wlanfreq=$(sudo wpa_cli -i$wlaninterface status | grep "freq")
		if [ "$managefrequency" == "0" ]
		then
			wlanfreq=""
		fi
		if [ "$wlanfreq" != "" ]
		then	
			echo $wlaninterface": "$wlanfreq
			echo "Setting up wifi p2p with "$wlanfreq
		fi
		while [ `echo "${ain}" | grep -c "p2p-wl"`  -lt 1 ] 
		do
			while [ `echo "${ain}" | grep -c "p2p-wl"`  -lt 1 ]
			do
				#sudo wpa_cli p2p_group_add -i$p2pdevinterface persistent$perstr freq=2
				result=$(sudo wpa_cli p2p_group_add -i$p2pdevinterface persistent$perstr $wlanfreq)
				if [ "$result" == "FAIL" ]					
				then
					wlanfreq=""
					managefrequency=0
				fi
				sleep 2
				ain="$(sudo wpa_cli interface)"
				echo "$ain"
			done
			sleep 5
			ain="$(sudo wpa_cli interface)"
		    echo "$ain"
		done

	fi

	p2pinterface=$(echo "${ain}" | grep "p2p-wl" | grep -v "interface")
	echo $p2pinterface

	sudo ifconfig $p2pinterface 192.168.173.1
	printf "start	192.168.173.80\n">udhcpd.conf
	printf "end	192.168.173.80\n">>udhcpd.conf
	printf "interface	$p2pinterface\n">>udhcpd.conf
	printf "option subnet 255.255.255.0\n">>udhcpd.conf
	printf "option lease 10">>udhcpd.conf
	sleep 3
	sudo busybox udhcpd ./udhcpd.conf 
	echo "The display is ready"
	echo "Your device is called: "$(uname -n)""
	while :
	do	
		echo "PIN:"	
		sudo wpa_cli -i$p2pinterface wps_pin any 31415926
		echo ""
		./d2.py
		if [ `sudo wpa_cli interface | grep -c "p2p-wl"` == 0 ] 
		then
			break
		fi
		
		wlanfreq=$(sudo wpa_cli -i$wlaninterface status | grep "freq")
		p2pfreq=$(sudo wpa_cli -i$p2pinterface status | grep "freq")
		if [ "$managefrequency" == "0" ]
		then
			wlanfreq=""
		fi
		if [ "$wlanfreq" != "" ]
		then		
			if [ "$wlanfreq" != "$p2pfreq" ] 
			then
				echo "The display is disconnected since "$wlaninterface" changes from "$p2pfreq" to "$wlanfreq
				echo "To disable WLAN roaming, run: sudo killall -STOP NetworkManager"
				echo "You can re-enable roaming afterwards by running: sudo killall -CONT NetworkManager"
				sudo wpa_cli -i$p2pinterface p2p_group_remove $p2pinterface
				while :
				do
					if [ `sudo wpa_cli interface | grep -c "p2p-wl"` == 0 ] 
					then
						break
					fi
				done
				break
			fi
		fi

	done
done
