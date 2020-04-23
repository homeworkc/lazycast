#!/bin/bash

p2pinterface=$(sudo wpa_cli interface | grep "p2p-wl" | grep -v "interface")
echo $p2pinterface
sudo wpa_cli -i$p2pinterface p2p_group_remove $p2pinterface
while :
do
	if [ `sudo wpa_cli interface | grep -c "p2p-wl"` == 0 ] 
	then
		break
	fi
done
