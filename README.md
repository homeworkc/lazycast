lazycast: A Simple Wireless Display Receiver

# Description
lazycast is a simple wifi display receiver. It was originally targeted Raspberry Pi (as display) and Windows 8.1/10 (as source), but it **might** work with other Linux distros and Miracast sources, too. In general, lazycast does not require re-compilation of wpa_supplicant to provide p2p capability, and should work on an "out of the box" Raspberry Pi.

# Required package
net-tools python udhcpd

Note: udhcpd is a DHCP server for Ubuntu and Debian.  
Note: Two in-house players are written for Raspberry Pi 3. You may use omxplayer or vlc on other platforms.

# Preparation
Install missing packages  
Make all.sh, d2.py, player.bin, control.bin, and controlhidc.bin executable: 
```
chmod +x all.sh
chmod +x d2.py
cd player
chmod +x player.bin
cd ../h264
chmod +x h264.bin
cd ../control
chmod +x control.bin
chmod +x controlhidc.bin
```
# Usage
Run `./all.sh` to initiate lazycast receiver. Wait until the "The display is ready" message.  
Then, search for the wireless display named "lazycast" on the source device you want to cast. Use the PIN number under the "The display is ready" message if the device is asking a WPS PIN number.  
If backchannel control is supported by the source, keyboard and mouse input on Pi are redirected to the source as remote controls.  
It is recommended to initiate the termination of the receiver on the source side. These user controls are often near the pairing controls on the source device. You can utilize the backchannel feature to remotely control the source device in order to close lazycast.  

# Tips
The pairing process (entering PIN) is needed after every Raspberry Pi reboot. Try clearing the 'lazycast' information on the source device if you run into pairing problems.  
Initial pairings after Raspberry Pi reboot may be difficault due to ARP/routing/power-saving mechanisms. Try turning off/on WiFi interfaces on the source device and re-pairing. If all else fails, reboot both the source and Pi and pair them upon starting.  
The PIN number will be invalid after about 2 mins. Re-run all.sh in this scenario.  
Set the resolution on the source side. lazycast advertises all possible resolutions regardless of the current rendering resolutions. Therefore, you may want to change the resolution (on the source) to match the actual resolution of the display connecting to Pi.  
Modify parameters in the "settings" section in d2.py to change sound output port (hdmi/3.5mm) and preferable player.
The maximum resolutions supported are 1920x1080p60 and 1920x1200p30. The GPU on Pi may struggle to handle 1920x1080p60, which results in high latency. In this case, reduce the FPS to 1920x1080p50.  

# Known issue
Latency: Limited by the implementation of the rtp player used. (In VLC, latency can be reduced from 1200 to 300ms by lowering the network cache value.)  
The on-board WiFi chip on Pi 3 only supports 2.4GHz. Therefore, devices/protocols that use 5.8GHz for P2P communication (e.g. early generations of WiDi) are not ("out of the box") supported.  
Due to the overcrowded nature of the 2.4GHz spectrum and the use of unreliable rtp transmission, you may experience some video glitching/audio stuttering. The in-house players employ several mechanisms to conceal transmission error, but it may still be noticeable in challenging wireless environments.  
Devices may not fully support backchannel control and some keystroke/click will behave differently in this scenario.  
HDCP(content protection): Neither the key nor the hardware is available on Pi and therefore is not supported.  

# Start on boot
Change the first line of code in ``all.sh`` to match the current directory of lazycast. For example, if lazycast is placed on ``~/Desktop``, change the first line to:
```
cd ~/Desktop/lazycast
```
Then, append this line to ``~/.config/lxsession/LXDE-pi/autostart``
```
@lxterminal -l -e ~/Desktop/lazycast/all.sh
```

# Others
Some parts of the video player1 are modified from the codes on https://github.com/Apress/raspberry-pi-gpu-audio-video-prog. Many thanks to the author of "Raspberry Pi GPU Audio Video Programming" and, by extension, authors of omxplayer.  
Using any part of the codes in this project in commercial products is prohibited.
