lazycast: A Simple Wireless Display Receiver

# Description
lazycast is a simple wifi display receiver. It was originally targeted Raspberry Pi (as display) and Windows 8.1/10 (as source), but it **might** work with other Linux distros and Miracast sources, too. In general, it does not require re-compilation of wpa_supplicant to provide p2p capability, and should work on an "out of the box" Raspberry Pi.

# Required package
net-tools python udhcpd omxplayer(on Pi, use vlc on other platforms)

Note: udhcpd is a DHCP server for Ubuntu and Debian.  
Note: use omxplayer on Raspberry Pi for HW acceleration  

# Usage
Make all.sh executable: `chmod +x all.sh`  
Run `./all.sh` to initiate lazycast receiver. Wait until the "The display is ready" message.
Then, search for the wireless display named "lazycast" on the device you want to cast. Use the pin number under the "The display is ready" message if the device is asking a WPS pin number.  


# Known issue
Latency: Limited by the implementation of the rtp client used. (In VLC, latency can be reduced from 1200 to 300ms by lowering the network cache value.)  
omxplayer unexpected quit: Execute `omxplayer -b --avdict rtsp_transport:tcp rtp://0.0.0.0:1028/wfd1.0/streamid=0 --live --threshold 0.05 --timeout 10000` manually until the screen is displayed.  
omxplayer doesn't render smoothly for win 8 source.  
The in-house player have long transition time (e.g., resolution changes) for win 8 sources since ffmpeg drops packets with non-continuous seq number.


# TODO 
Detect which dhcp server program to use  
UIBC: (feed cursor and keystroke back to source)  
Latency reduction  
