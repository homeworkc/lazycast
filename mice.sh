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
ain="$(sudo wpa_cli interface)"
echo "${ain}"
if [ `echo "${ain}" | grep -c "p2p-wl"` -gt 0 ] 
then
	p2pinterface=$(echo "${ain}" | grep "p2p-wl" | grep -v "interface")

	sudo wpa_cli p2p_group_remove $p2pinterface
fi
sleep 10
sudo wpa_cli p2p_find type=progessive
sudo wpa_cli set device_name "$(uname -n)"
sudo wpa_cli set device_type 7-0050F204-1
sudo wpa_cli set p2p_go_ht40 1
sudo wpa_cli wfd_subelem_set 0 00060151022a012c
sudo wpa_cli wfd_subelem_set 1 0006000000000000
sudo wpa_cli wfd_subelem_set 6 000700000000000000
./setvendor.py

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

p2pinterface=$(echo "${ain}" | grep "p2p-wl" | grep -v "interface")
echo $p2pinterface


sudo nc -l -p 7250
