#!/bin/bash +x
set -e

# This script has been tested with the "2020-02-05-raspbian-buster-lite" image.
#test super user
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

#install
echo "Installing dependencies..."
apt-get update
apt-get --yes install  git wpasupplicant libx11-dev libasound2-dev libavformat-dev libavcodec-dev python2
echo "done."

# Download lazycast  to /opt (or update if already present)
echo
cd /opt
if [ -d lazycast ]; then
  echo "Updating lazycast..."
  cd lazycast && git pull && git checkout ${1:master}
else
  echo "Downloading lazycast..."
  git clone https://github.com/amerinoj/lazycast.git
  cd lazycast && git checkout ${1:master}
fi
echo "done."

# Compile files
cd /opt/vc/src/hello_pi/libs/ilclient
make
cd /opt/vc/src/hello_pi/hello_video
make
cd /opt/lazycast
make

#Menu
opt=""
while [[ $opt != "End" ]]; do
	#clear
	echo '####################  Menu Config options  ####################'
	PS3='Config options: '
	options=("Audio" "Wireless card" "Pincode" "Bluetooth" "End")
	select opt in "${options[@]}"
	do
	    case $opt in
		"Audio")
		    #select audio output
                        echo -e "-------Audio config-------\n"
			AudioOuput="auto,headphones,hdmi"
			oldIFS=$IFS
			IFS=$','
			choices=($AudioOuput)
			IFS=$oldIFS
			PS3="Select your audio output :"
			select answer in "${choices[@]}"; do
			    for item in "${choices[@]}"; do
			       if [[ $item == $answer ]]; then
				    echo "Audio output select:"$answer
		                    break 2;
			       fi
			    done
			done
			Aoutput=$answer
			if [[ $Aoutput == "auto" ]]; then
			     amixer cset numid=3 0
			     sed -i 's/sound_output_select = ./sound_output_select = 2/g' /opt/lazycast/d2.py	
			else
			     if [[ $Aoutput == "hdmi" ]]; then
				 amixer cset numid=3 2
				 sed -i 's/sound_output_select = ./sound_output_select = 0/g' /opt/lazycast/d2.py
			     else
				 if [[ $Aoutput == "headphones" ]]; then
				     amixer cset numid=3 1
				     sed -i 's/sound_output_select = ./sound_output_select = 1/g' /opt/lazycast/d2.py
				 fi
			     fi	
			fi
		    break
		    ;;
		"Wireless card")
			#select wlan
			echo -e "-------Wireless card config-------\n"
		    	listcard=$(iw dev | grep wlan  | cut -d" " -f2 )
			oldIFS=$IFS
			IFS=$'\n'
			choices=($listcard)
			IFS=$oldIFS
			PS3="Select your wireless card: "
			select answer in "${choices[@]}"; do
			  for item in "${choices[@]}"; do
			    if [[ $item == $answer ]]; then
		               break 2;
			    fi
			  done
			done
			wcard=$answer
			echo "Adapter select:"$wcard
			sed -i '/select_interface=/c\'select_interface="\"$wcard"\"'' /opt/lazycast/all.sh
			#update /etc/dhcpcd.conf
			for item in "${choices[@]}"; do
		  	  if [[ $item == $wcard ]]; then
				if  grep -q $wcard "/etc/dhcpcd.conf" ; then
                     		    sed -i "s/$wcard/$wcard \n    wpa_supplicant/g" /etc/dhcpcd.conf
                  		else
                     		   echo -e "interface  "$wcard"\n     wpa_supplicant" >> /etc/dhcpcd.conf
				fi 
			  else
				if  grep -q $item "/etc/dhcpcd.conf" ; then
                     		    sed -i "s/$item/$item \n    nohook wpa_supplicant/g" /etc/dhcpcd.conf
                		else
                     		    echo -e "interface  "$item"\n     nohook wpa_supplicant" >> /etc/dhcpcd.conf
				fi
			  fi
			done

			Local=$(locale | grep LANG= | cut -d"_" -f2)
			echo Your system locale is:$Local
			echo Assigning locale as country code to wireless card
			iw reg set $Local

			if ! grep -q "ctrl_interface=" "/etc/wpa_supplicant/wpa_supplicant.conf" ; then
			    sed -i '1ictrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev' /etc/wpa_supplicant/wpa_supplicant.conf
			fi
			if ! grep -q "country=" "/etc/wpa_supplicant/wpa_supplicant.conf" ; then
			    echo 'country='$Local >> /etc/wpa_supplicant/wpa_supplicant.conf
			else
			    sed -i 's/country=../country='$Local'/g' /etc/wpa_supplicant/wpa_supplicant.conf
			fi
			sed -i 's/country=../country='$Local'/g' /etc/wpa_supplicant/wpa_supplicant.conf

			if ! grep -q "p2p_go_ht40=" "/etc/wpa_supplicant/wpa_supplicant.conf" ; then
			    echo 'p2p_go_ht40=1' >> /etc/wpa_supplicant/wpa_supplicant.conf
			else
			    sed -i 's/p2p_go_ht40=./p2p_go_ht40=1/g' /etc/wpa_supplicant/wpa_supplicant.conf
			fi
			if ! grep -q "update_config=" "/etc/wpa_supplicant/wpa_supplicant.conf" ; then
			    echo 'update_config=1' >> /etc/wpa_supplicant/wpa_supplicant.conf
			else
			    sed -i 's/update_config=./update_config=1/g' /etc/wpa_supplicant/wpa_supplicant.conf
			fi

		    break
		    ;;
		"Pincode")
			#config pincode
                        echo -e "-------Pincode config-------\n"            
			pincode=""
			chrlen=${#pincode}
			while [[ $chrlen -ne 8 ]]
			do
				read -p "Intro your pincode [8 digits] : " pincode
				chrlen=${#pincode}
				echo $chrlen
			done

			sed -i 's/pin="........"/'pin="\"$pincode"\"'/g' /opt/lazycast/all.sh
			echo Pincode save: $pincode;
		    break
		    ;;

		"Bluetooth")
			#config bluetooth
                        echo -e "-------Bluetooth config-------\n"            
			btopt="disable,enable,go back"
			oldIFS=$IFS
			IFS=$','
			choices=($btopt)
			IFS=$oldIFS
			PS3="Select your option :"
			select answer in "${choices[@]}"; do
			    for item in "${choices[@]}"; do
			       if [[ $item == $answer ]]; then
				    echo "Bluetooth:"$answer
		                    break 2;
			       fi
			    done
			done
			Btoutput=$answer
			if [[ $Btoutput == "disable" ]]; then
				#disable internal raspberry bluetooth
				echo "blacklist btbcm" >> /etc/modprobe.d/bluetooth-blacklist.conf 
				echo "blacklist hci_uart" >> /etc/modprobe.d/bluetooth-blacklist.conf	
			fi
			if [[ $Btoutput == "enable" ]]; then
				#enable internal raspberry bluetooth
				rm /etc/modprobe.d/bluetooth-blacklist.conf 
			fi


		    break
		    ;;
		"End")
		    break
		    ;;
		*) echo "invalid option $REPLY";;
	    esac
	done

done

# Install daemon
cp -n /opt/lazycast/lazycast.service /etc/systemd/system/lazycast.service
systemctl daemon-reload
systemctl  enable lazycast.service

# Finished
echo
echo "lazycast has been installed."
echo "Reboot the system to finish."
