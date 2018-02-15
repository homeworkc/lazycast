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
wlaninterface=wlo1
ain="$(sudo wpa_cli -i$wlaninterface interface)"
echo "${ain}"
if [ `echo "${ain}" | grep -c "p2p-wl"` -gt 0 ] 
then
	echo "already on"

else
	sudo wpa_cli p2p_find
	sudo wpa_cli set device_name lazycast
	sudo wpa_cli set device_type 7-0050F204-1
	sudo wpa_cli wfd_subelem_set 0 00060151022a012c
	sudo wpa_cli wfd_subelem_set 1 0006000000000000
	sudo wpa_cli wfd_subelem_set 6 000700000000000000
	while [ `echo "${ain}" |grep -c "p2p-wl"`  -lt 1 ] 
	do
		sudo wpa_cli p2p_group_add
		sleep 2
		ain="$(sudo wpa_cli -i$wlaninterface interface)"
		echo "$ain"
	done

fi

p2pinterface=$(echo "${ain}" | grep "p2p-wl")
echo $p2pinterface

sudo ifconfig $p2pinterface 192.168.101.1
sed -i -e "s/\(interface \).*/\1$p2pinterface/"   udhcpd.conf
sudo udhcpd ./udhcpd.conf 
sleep 1
echo "The display is ready"
sudo wpa_cli -i$p2pinterface wps_pin any
pingresult=$(ping 192.168.101.80 -I $p2pinterface -c 1 -W 1)
while [ `echo "${pingresult}" | grep -c "bytes from"` -lt 1 ] 
do
    pingresult=$(ping 192.168.101.80 -I $p2pinterface -c 1 -W 1)
done
./d2.py
