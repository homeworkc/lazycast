lazycast: A Simple Wireless Display Receiver for Raspberry Pi

# Description
lazycast is a simple wifi display receiver. It was originally targeted Raspberry Pi (as display) and Windows 8.1/10 (as source), but it **might** work with other linux distro and Miracast sources, too. In general, it does not require recompilation of wpa_supplicant to provide p2p capability, and should work "out of the box" with Raspberry Pi.

# Required package
net-tools python udhcpd omxplayer(on Pi, use vlc on other platforms)

Note: udhcpd is a DHCP server for Ubuntu and Debian.  
Note: use omxplayer on Raspberry Pi for HW acceleration  

# Usage

Run `./all.sh` to initiate lazycast receiver. Wait until the "The display is ready" message.
Then, search for the wireless display named "lazycast" on the device you want to cast. Use the pin number under the "The display is ready" message if the device is asking the WPS pin number.  


# Known issue
Latency: limited by the implementation of the rtp client used.
omxplayer unexpected quit: 



# TODO
UIBC: (feed cursor and keystroke back to source)
Latency reduction
