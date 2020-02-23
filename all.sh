#!/bin/bash +x
# uncomment next line to debug
#set -x
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
pin="31415926"
ip_neighbor="192.168.173.2"
ip_interface="192.168.173.1"
mask="255.255.255.252"
select_interface="wlan0"
Device_name="$(uname -n)"
################################################
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
#Main

#select interfaces
wpa_cli interface $select_interface

wpa_status="$(wpa_cli status)"
#get the current P2P mac address asigned to interface
mac_p2p="$(echo "${wpa_status}" | grep "p2p_device_address=" | cut -d"=" -f2 )"

net_id=""
if [[ $wpa_status !=  *"mode=P2P GO"*"wpa_state=COMPLETED"* ]]; then
                wpa_cli set device_name DIRECT-$Device_name
                wpa_cli set device_type 7-0050F204-1
                #wpa_cli set p2p_go_ht40 1
                wpa_cli set p2p_ssid_postfix  p2p-$Device_name

                echo "configuring WPA_supplicant"
		
                previous_nets="$(wpa_cli list_networks)"
                match_addr="$(echo "${previous_nets}" | grep "\[DISABLED\]\[P2P-PERSISTENT\]" | grep $mac_p2p)"
                
                #check if exist a previous network define with mac-address interfaces 
                if [[ $match_addr == *"DIRECT"*p2p-$Device_name*  ]] ;then
                      echo "Previous net_id Found..."
                      net_id=$(echo "${match_addr}" | cut -d$'\t' -f1 | head -n 1)
                      echo "Previous net_id Found: "$net_id
                      wpa_cli p2p_group_add persistent=$net_id

                else
                # id no found with mac address interface
                    # searching old P2P network profile
                   any_net="$(echo "${previous_nets}" | grep "\[DISABLED\]\[P2P-PERSISTENT\]" | grep "DIRECT" )"
                   if [[ $any_net == *"DIRECT"*p2p-$Device_name*  ]] ;then
                        net_id=$(echo "${any_net}" | cut -d$'\t' -f1 | head -n 1)
                        echo "Reusing old net_id":$net_id
                       
                        delete_nets=$(echo "${any_net}" | cut -d$'\t' -f1 | tail -n +2)
            
                        for old_net in $delete_nets
                        do
                           echo "Removing others network id: "$old_net
                           wpa_cli remove_network $old_net
                        done
                       	
                        wpa_cli save_config
                        wpa_cli p2p_group_add persistent=$net_id
                        sleep 1
                   else
                        # No P2P network found in wpa_supplicant.conf
                        echo "No found P2P network "
                        echo "Creating new ..."
                        wpa_cli p2p_group_add persistent
                   fi

                fi

                wpa_cli wfd_subelem_set 0 000600111c44012c
                wpa_cli wfd_subelem_set 1 0006000000000000
                wpa_cli wfd_subelem_set 6 000700000000000000


                
fi
              

# get real interfaces name
interface=$( wpa_cli status | grep "Selected interface" | cut -d"'" -f2 )

#check if the interface is ok
if [[  "$(iw dev $interface info 2>&1)" !=  *"No such device"*  ]]; then
                
       if [[ "$(iw dev $interface info 2>&1 | grep type)" ==  *"P2P"* ]]; then
            echo "Interface UP:"$interface " in P2P mode"
       else
            echo "Interface UP:"$interface "but not in P2P mode"
       fi
else
       echo Device error:$interface
       exit
fi

echo "WPA config in P2P mode"
echo $interface
		
ifconfig $interface $ip_interface
ifconfig $interface netmask $mask

echo "The display is ready"
echo "Your device is called: DIRECT-"$Device_name
echo "PIN-->"     
wpa_cli wps_pin -i$interface any $pin
echo "<--PIN"

echo "Waiting connection"
./d2.py -i$ip_interface -m$mask -p$ip_neighbor   -d$interface

#clear p2p connection and arp entry
echo "Connection Finished"
ip neigh flush  $ip_neighbor

