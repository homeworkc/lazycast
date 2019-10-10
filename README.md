lazycast: A Simple Wireless Display Receiver

# Description
lazycast is a simple wifi display receiver. It was originally targeted Raspberry Pi (as display) and Windows 8.1/10 (as source), but it **might** work with other Linux distros and Miracast sources, too. In general, lazycast does not require re-compilation of wpa_supplicant to provide p2p capability, and should work on an "out of the box" Raspberry Pi.

# Required package
udhcpd

Note: udhcpd is a DHCP server for Ubuntu and Debian.  
Note: Two in-house players are written for Raspberry Pi 3. You may use omxplayer or vlc on other platforms.

# Preparation
**The wpa_supplicant installed on the latest Raspbian distribution does not seem to work properly. (See [this](https://www.reddit.com/r/linux4noobs/comments/c5qila/want_to_downgrade_wpa_supplicant/).) For Raspbian Buster, try downgrading the ``wpasupplicant`` package to the version for Raspbian Stretch. Here is one solution:**
```
wget http://ftp.us.debian.org/debian/pool/main/w/wpa/wpasupplicant_2.4-1+deb9u4_armhf.deb
sudo apt --allow-downgrades install ./wpasupplicant_2.4-1+deb9u4_armhf.deb
```  
Install missing packages:  
```
sudo apt install udhcpd
```
Download the latest release from https://github.com/homeworkc/lazycast/releases.  
Make all.sh, d2.py, player.bin, h264.bin, control.bin, and controlhidc.bin executable: 

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
# Compile from Source
The following steps are only required if you want to compile the binaries from source.
```
sudo apt install libx11-dev libasound2-dev libavformat-dev libavcodec-dev
cd /opt/vc/src/hello_pi/libs/ilclient/
make
cd /opt/vc/src/hello_pi/hello_video
make
```
Then follow the steps from the previous section.


# Usage
Run `./all.sh` to initiate lazycast receiver. Wait until the "The display is ready" message.
The name of your device will also be displayed on the pi.
Then, search for the wireless display on the source device you want to cast. The default PIN number is ``31415926``.  
If backchannel control is supported by the source, keyboard and mouse input on Pi are redirected to the source as remote controls.  
It is recommended to initiate the termination of the receiver on the source side. These user controls are often near the pairing controls on the source device. You can utilize the backchannel feature to remotely control the source device in order to close lazycast.  

## Automatic startup / SystemD

You can run lazycast when booting your Pi using the [systemd unit](lazycast.service). To install, log into your Pi and run:

```bash
git clone https://github.com/homeworkc/lazycast.git
mkdir -p ~/.config/systemd/user
cp lazycast/lazycast.service ~/.config/systemd/user/
systemctl --user enable lazycast.service
systemctl --user start lazycast.service
```

NOTE: The systemd unit expects lazycast to be located under `/home/pi/lazycast`, adjust the WorkingDirectory if this is not the correct path.

# Tips
Initial pairings after Raspberry Pi reboot may be difficault due to ARP/routing/power-saving mechanisms. Try turning off/on WiFi interfaces on the source device and re-pairing. If all else fails, reboot both the source and Pi and pair them upon boot.  
Set the resolution on the source side. lazycast advertises all possible resolutions regardless of the current rendering resolution. Therefore, you may want to change the resolution (on the source) to match the actual resolution of the display connecting to Pi.  
Modify parameters in the "settings" section in ``d2.py`` to change the sound output port (hdmi/3.5mm) and preferred player.  
The maximum resolutions supported are 1920x1080p60 and 1920x1200p30. The GPU on Pi may struggle to handle 1920x1080p60, which results in high latency. In this case, reduce the FPS to 1920x1080p50.  
After Pi connects to the source, it has an IP address of ``192.168.173.1`` and this connection can be reused for other purposes like SSH or USB over IP. 

# Known issues
lazycast tries to remember the pairing credentials so that entering the PIN is only needed once for each device. However, this feature does not seem to work properly all the time with recent Raspbian images. (Using the latest Raspbian is still recommended from the security perspective. However, recent Raspbians randomize the MAC address of the ``p2p-dev-wlan0`` interface upon reboot, while old Raspbians ([example](https://downloads.raspberrypi.org/raspbian/images/raspbian-2017-09-08/)) do not. **Any insights or suggestions on this issue are appreciated**, and could make this important feature work again.) Therefore, re-pairing may be needed after every Raspberry Pi reboot. Try clearing the 'lazycast' information on the source device before re-pairing if you run into pairing problems.  
Latency: Limited by the implementation of the rtp player used. (In VLC, latency can be reduced from 1200 to 300ms by lowering the network cache value.)  
The on-board WiFi chip on Pi 3 only supports 2.4GHz. Therefore, devices/protocols that use 5.8GHz for P2P communication (e.g. early generations of WiDi) are not ("out of the box") supported.  
Due to the overcrowded nature of the 2.4GHz spectrum and the use of unreliable rtp transmission, you may experience some video glitching/audio stuttering. The in-house players employ several mechanisms to conceal transmission error, but it may still be noticeable in challenging wireless environments.  
Devices may not fully support backchannel control and some keystrokes/clicks will behave differently in this case.  
HDCP(content protection): Neither the key nor the hardware is available on Pi and therefore is not supported.  

# Start on boot
Append this line to ``/etc/xdg/lxsession/LXDE-pi/autostart``:
```
@lxterminal -l --working-directory=<absolute path of lazycast> -e ./all.sh
```
For example, if lazycast is placed on ``/home/pi/Desktop``, append the following line to the file:
```
@lxterminal -l --working-directory=/home/pi/Desktop/lazycast -e ./all.sh
```


# Others
Some parts of the video player1 are modified from the codes on https://github.com/Apress/raspberry-pi-gpu-audio-video-prog. Many thanks to the author of "Raspberry Pi GPU Audio Video Programming" and, by extension, authors of omxplayer.  
Using any part of the codes in this project in commercial products is prohibited.
