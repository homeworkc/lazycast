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
cd ~/Desktop/lazycast
ain="$(sudo wpa_cli interface)"
echo "${ain}"
if [ `echo "${ain}" | grep -c "p2p-wl"` -gt 0 ] 
then
	echo "already on"

else
	sudo wpa_cli p2p_find
	sudo wpa_cli set device_name lazycast
	sudo wpa_cli set device_type 7-0050F204-1
	sudo wpa_cli set p2p_go_ht40 1
	sudo wpa_cli wfd_subelem_set 0 00060151022a012c
	sudo wpa_cli wfd_subelem_set 1 0006000000000000
	sudo wpa_cli wfd_subelem_set 6 000700000000000000
	while [ `echo "${ain}" | grep -c "p2p-wl"`  -lt 1 ] 
	do
		while [ `echo "${ain}" | grep -c "p2p-wl"`  -lt 1 ]
        	do
			sudo wpa_cli p2p_group_add
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

sudo ifconfig $p2pinterface 192.168.101.1
printf "start	192.168.101.80\n">udhcpd.conf
printf "end	192.168.101.80\n">>udhcpd.conf
printf "interface	$p2pinterface\n">>udhcpd.conf
printf "option subnet 255.255.255.0\n">>udhcpd.conf
printf "option lease 60">>udhcpd.conf
sleep 3
sudo udhcpd ./udhcpd.conf 
echo "The display is ready"
sudo wpa_cli -i$p2pinterface wps_pin any
pingresult=$(ping 192.168.101.80 -I $p2pinterface -c 1 -W 1)
while [ `echo "${pingresult}" | grep -c "bytes from"` -lt 1 ] 
do
    pingresult=$(ping 192.168.101.80 -I $p2pinterface -c 1 -W 1)
done
./d2.py
