Lazycast: A Simple Wireless Display Receiver

# Description
lazycast is a simple wifi display receiver. It was originally targeted Raspberry Pi (as display) and Windows 8.1/10 or Android (as source) , but it **might** work with other Linux distros and Miracast sources, too. In general, lazycast does not require re-compilation of wpa_supplicant to provide p2p capability, and should work on an "out of the box" Raspberry Pi.

**It is also highly recommended use a external dongle, raspberry 3 use a common wifi/bluetooth BCM43438 and this cause issues when the bluetooth is enable**

# Preparation
**Working with wpa_supplicant v2.8-devel and dhcpcd 8.1.2 For raspbian Buster**

**UPGRADE YOUR PI3**
```
sudo apt-get update
sudo apt-get upgrade
```

**DEFINE THE INTERFACE**
- Modify the /etc/dhcpcd.conf file to include "wpa_supplicant" line in the wifi adapter to work with WPA_SUPPLICANT and exclude others with line "nohook wpa_supplicant" **
- In /etc/dhcpcd.conf you can specified the ip address to other adapters 

- For example to use a external dongle wlan1 to P2P wifi direct and wlan0 to HOSTAP:

nano /etc/dhcpcd.conf
```
interface wlan0
	static ip_address=192.168.42.1/24
	static routers=192.168.42.1
	static domain_name_servers=8.8.8.8 8.8.4.4
	nohook wpa_supplicant

interface wlan1
        wpa_supplicant

``` 
**CONFIG WPA_SUPPLICANT**
- Add this config to /etc/wpa_supplicant/wpa_supplicant.conf
- You can change the device_name=<Your_device_name> and  country=<Your_contry_code>, the contry code sould be same as the country define in raspi-conf
nano /etc/wpa_supplicant/wpa_supplicant.conf
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
device_name=DIRECT-SOUND-CARD
device_type=7-0050F204-1
p2p_go_ht40=1
country=ES

```  

**CHECK OTHER DHCP SERVICES**
- Lazycast has ower dhcp server integrated, make sure no other DHCP server is running in the system as  dnsmasq 
  if you are using another dhcp server for other projects, make sure is not in use under the interface selected  to lazycast, use "bind config" to separate the dhcp listening interfaces.
- For example in dnsmasq.conf you can use "bind-dynamic" parameter to exclude anyinterface as eth0 and wlan1 and only use dnsmasq in one interface.
nano /etc/dnsmasq.conf
```
bind-dynamic
no-dhcp-interface=eth0
no-dhcp-interface=wlan1
interface=wlan0
dhcp-range=interface:wlan0,192.168.42.10,192.168.42.50,255.255.255.0,24h
```


**INSTALL**
- Install packages used to compile the players:
```
sudo apt install libx11-dev libasound2-dev libavformat-dev libavcodec-dev
```
Compile libraries on Pi:
```
cd /opt/vc/src/hello_pi/libs/ilclient/
make
cd /opt/vc/src/hello_pi/hello_video
make
```
Then reboot.

Clone this repo (to a desired directory):
```
cd ~/
git clone https://github.com/homeworkc/lazycast
```
Go to the ``lazycast`` directory then ``make``:
```
cd lazycast
make
```

# Customize
Change the pin code and  ip address, modify all.sh and change the pin code.
You can change the ip address for p2p connection or leave it as it is .
```
# define options
pin="69696969"
ip_neighbor="192.168.173.2"
ip_interface="192.168.173.1"
mask="255.255.255.252"
```
# Usage
Run `sudo ./all.sh` to initiate lazycast receiver. Wait until the "The display is ready" message.
The name of your device will also be displayed on the pi and the wifi adapter used.
Then, search for the wireless display on the source device you want to cast. The default PIN number is ``69696969``.  
If backchannel control is supported by the source, keyboard and mouse input on Pi are redirected to the source as remote controls.  
It is recommended to initiate the termination of the receiver on the source side. These user controls are often near the pairing controls on the source device. You can utilize the backchannel feature to remotely control the source device in order to close lazycast.  



# Tips
Set the resolution on the source side. lazycast advertises all possible resolutions regardless of the current rendering resolution. Therefore, you may want to change the resolution (on the source) to match the actual resolution of the display connecting to Pi.  
Modify parameters in the "settings" section in ``d2.py`` to change the sound output port (hdmi/3.5mm) and preferred player.  
The maximum resolutions supported are 1920x1080p60 and 1920x1200p30. The GPU on Pi may struggle to handle 1920x1080p60, which results in high latency. In this case, reduce the FPS to 1920x1080p50.  
To change the default PIN number, replace the string ``69696969`` in ``all.sh`` to another 8-digit number.  
To eneble debuging output  change level_name='info' to level_name='debug'in ``all.sh`` also you can define the file save the output
After Pi connects to the source, it has an IP address of ``192.168.173.1`` and this connection can be reused for other purposes like SSH. On the other hand, since they are under the same subnet, precautions should be taken to prevent unauthorized access to Pi by anyone who knows the PIN number.    
Two in-house players are written for Raspberry Pi 3. Omxplayer or vlc can be used instead on other platforms. 


# Known issues
lazycast tries to remember the pairing credentials so that entering the PIN is only needed once for each device. However, this feature does not seem to work properly all the time with recent Raspbian images. (Using the latest Raspbian is still recommended from the security perspective. However, recent Raspbians randomize the MAC address of the ``p2p-dev-wlan0`` interface upon reboot, while old Raspbians ([example](https://downloads.raspberrypi.org/raspbian/images/raspbian-2017-09-08/)) do not. **Any insights or suggestions on this issue are appreciated**, and could make this important feature work again.) Therefore, re-pairing may be needed after every Raspberry Pi reboot. Try clearing the 'lazycast' information on the source device before re-pairing if you run into pairing problems.  
Latency: Limited by the implementation of the rtp player used. (In VLC, latency can be reduced from 1200 to 300ms by lowering the network cache value.)  
The on-board WiFi chip on Pi 3 only supports 2.4GHz. Therefore, devices/protocols that use 5.8GHz for P2P communication (e.g. early generations of WiDi) are not ("out of the box") supported.  
Due to the overcrowded nature of the wifi spectrum and the use of unreliable rtp transmission, you may experience some video glitching/audio stuttering. The in-house players employ several mechanisms to conceal transmission error, but it may still be noticeable in challenging wireless environments. Interference from other devices may cause disconnections.  
Devices may not fully support backchannel control and some keystrokes/clicks will behave differently in this case. The left Windows key is not captured and when it is pressed, it makes the current window to be out-of-focus and thus disables the backchannel controls. If it is pressed again the window will be in-focus.   
HDCP(content protection): Neither the key nor the hardware is available on Pi and therefore is not supported.  
In some phone the wifi chipset is share with bluetooth, if you experiment lag disable the bluetooth in your phone after the P2P connection will be created.

# Start on boot

## Method 1:
Append this line to ``/etc/xdg/lxsession/LXDE-pi/autostart``:
```
@lxterminal -l --working-directory=<absolute path of lazycast> -e ./all.sh
```
For example, if lazycast is placed under ``~/`` (which corresponds to ``/home/pi/``), append the following line to the file:
```
@lxterminal -l --working-directory=/home/pi/lazycast -e ./all.sh
```


## Method 2: SystemD

You can run lazycast when booting your Pi using the [systemd unit](lazycast.service). To install, log into your Pi and run:

```bash
git clone https://github.com/homeworkc/lazycast.git
mkdir -p ~/.config/systemd/user
cp lazycast/lazycast.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable lazycast.service
systemctl --user start lazycast.service
sudo loginctl enable-linger pi
```

NOTE: In this method, the systemd unit expects lazycast to be located under `/home/pi/lazycast`, adjust the WorkingDirectory if this is not the correct path.


# Others
Some parts of the video player1 are modified from the codes on https://github.com/Apress/raspberry-pi-gpu-audio-video-prog. Many thanks to the author of "Raspberry Pi GPU Audio Video Programming" and, by extension, authors of omxplayer.  
Using any part of the codes in this project in commercial products is prohibited.
The dhcp server was based on the proyect https://github.com/pypxe/PyPXE

# Fixes
This version fix the next issues 

all.sh:
-	Now detect other wireless cards that are manager by wpa_supplicant.
 using a external dongle and when the wireless card is put in p2p mode the interface name is not change it, but we can use "iw dev type" to identify the mode.

D2.py:
- Add overload parameters  :
interface ip address
interface mask
interface name
neighbor peer address

invoke  ( d2.py -i <self_ip_address> -m <mask> -d <device> -p <ip_peer_address>)
This fix some problems, sometimes the connection tried to establish through another network card, now when the sock is created the interface name is passed to ensure the connection is open to the correct interface 

- Timeouts and payloads modified in the socket objects
The sockets has delimiter the timeout and the payload size these changes permit optimize the load and quality in the connection. Also when you press Ctr+^C or the System send a signal to close the proccess to shutdown the program can ear it and exit in correct order.

- Integrated DHCP server.
Now is not need use a external DHCP to assign Ip address to a peer neighbor. The code has integrate "dhcpserver.py" this is a modified version of "PyPXE" proyect.
https://github.com/pypxe/PyPXE
The original code was modified to assignen P2P addres "/30" and asing always the same address to diferents neigbors. 
This permit a exact control of address assigned and permit renew the leased time of dhcp servers.

The dhcpserver.py is controller by threading in main program.


-Catch exceptions
Now the code has a complete Catch exceptions and will finish right if a exception is detected. All sockets will be close and the all subprocess will be end

-Debug
level_name='info'
Implemented python logging. Now you can define the information level to debug the code, or put in "info" level to normal use.

-lazycast.service
As now the main program only management one connection per launch. 
The lazycast service restart the application when detect a exit code.
Restart=always
RestartSec=2s
lazycast.service was modified to intergrate the daemon  in the main systemctl.

- h264.c
Was suppressed the message "sound error " when only video is transmitter.


