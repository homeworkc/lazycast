lazycast: A Simple Wireless Display Receiver

# Description
lazycast is a simple wifi display receiver. It was originally targeted Raspberry Pi (as display) and Windows 8.1/10 (as source), but it **might** also work on other Linux platforms and Miracast sources. (For other Linux systems, skip the preparation section.) In general, lazycast does not require re-compilation of wpa_supplicant to provide p2p capability, and should work on an "out of the box" Raspberry Pi.

# Preparation
## Downgrade wpa_supplicant
**The wpa_supplicant installed on the latest Raspbian distribution does not seem to work properly. (See [this](https://www.reddit.com/r/linux4noobs/comments/c5qila/want_to_downgrade_wpa_supplicant/).) For Raspbian Buster, try downgrading the ``wpasupplicant`` package to the version for Raspbian Stretch. Here is one solution:**
```
wget http://ftp.us.debian.org/debian/pool/main/w/wpa/wpasupplicant_2.4-1+deb9u4_armhf.deb
sudo apt --allow-downgrades install ./wpasupplicant_2.4-1+deb9u4_armhf.deb
```  
## Install NetworkManager
**It is also highly recommended to replace the "Wireless & Wired Network" in Raspbian with NetworkManager, which can maintain much more stable p2p connection. Here is one solution (adopted from [here](https://raspberrypi.stackexchange.com/questions/29783/how-to-setup-network-manager-on-raspbian)):**
```
sudo apt install network-manager network-manager-gnome openvpn openvpn-systemd-resolved network-manager-openvpn network-manager-openvpn-gnome
```
And,
```
sudo apt purge dhcpcd5
```
Additionally, ``systemd-resolved`` should be disabled since it does not seem to work well with NetworkManager, which causes DNS problems. (See [here](https://unix.stackexchange.com/questions/518266/ping-displays-name-or-service-not-known) for details.) (It may take a while for the problems to show).
```
sudo systemctl disable systemd-resolved
```
Then reboot:
```
sudo reboot
```
## Compile Source
Install packages used to compile the players:
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
Clone this repo (to a desired directory):
```
cd ~/
git clone https://github.com/homeworkc/lazycast
```
Go to the ``lazycast`` directory and then ``make``:
```
cd lazycast
make
```

# Usage
Run `./all.sh` to initiate lazycast receiver. Wait until the "The display is ready" message.
The name of your device will also be displayed on the pi.
Then, search for the wireless display on the source device you want to cast. The default PIN number is ``31415926``.  
If backchannel control is supported by the source, keyboard and mouse input on Pi are redirected to the source as remote controls.  
It is recommended to initiate the termination of the receiver on the source side. These user controls are often near the pairing controls on the source device. You can utilize the backchannel feature to remotely control the source device in order to close lazycast.  



# Tips
Set the resolution on the source side. lazycast advertises all possible resolutions regardless of the current rendering resolution. Therefore, you may want to change the resolution (on the source) to match the actual resolution of the display connecting to Pi.  
Modify parameters in the "settings" section in ``d2.py`` to change the sound output port (hdmi/3.5mm) and preferred player.  
The maximum resolutions supported are 1920x1080p60 and 1920x1200p30. The GPU on Pi may struggle to handle 1920x1080p60, which results in high latency. In this case, reduce the FPS to 1920x1080p50.  
To change the default PIN number, replace the string ``31415926`` in ``all.sh`` to another 8-digit number.  
After Pi connects to the source, it has an IP address of ``192.168.173.1`` and this connection can be reused for other purposes like SSH. On the other hand, since they are under the same subnet, precautions should be taken to prevent unauthorized access to Pi by anyone who knows the PIN number.    
Two in-house players are written for Raspberry Pi 3. VLC, omxplayer or gstreamer can be used instead on other platforms. (See [here](https://gstreamer.freedesktop.org/documentation/installing/on-linux.html) for details of installing gstreamer.) 


# Known issues
lazycast tries to remember the pairing credentials so that entering the PIN is only needed once for each device. However, this feature does not seem to work properly all the time with recent Raspbian images. (Using the latest Raspbian is still recommended from the security perspective. However, recent Raspbians randomize the MAC address of the ``p2p-dev-wlan0`` interface upon reboot, while old Raspbians ([example](https://downloads.raspberrypi.org/raspbian/images/raspbian-2017-09-08/)) do not. **Any insights or suggestions on this issue are appreciated**, and could make this important feature work again.) Therefore, re-pairing may be needed after every Raspberry Pi reboot. Try clearing the 'lazycast' information on the source device before re-pairing if you run into pairing problems.  
Latency: Limited by the implementation of the rtp player used. (In VLC, latency can be reduced from 1200 to 300ms by lowering the network cache value.)  
The on-board WiFi chip on Pi 3 only supports 2.4GHz. Therefore, devices/protocols that use 5.8GHz for P2P communication (e.g. early generations of WiDi) are not ("out of the box") supported.  
Due to the overcrowded nature of the wifi spectrum and the use of unreliable rtp transmission, you may experience some video glitching/audio stuttering. The in-house players employ several mechanisms to conceal transmission error, but it may still be noticeable in challenging wireless environments. Interference from other devices may cause disconnections.  
Devices may not fully support backchannel control and some keystrokes/clicks will behave differently in this case. The left Windows key is not captured and when it is pressed, it makes the current window to be out-of-focus and thus disables the backchannel controls. If it is pressed again the window will be in-focus.   
HDCP(content protection): Neither the key nor the hardware is available on Pi and therefore is not supported.  

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

# Miracast over Infrastructure
For Windows 10 sources, Miracast over Infrastructure (MICE) is a feature that allows transmission of screen data over Ethernet or secure wifi networks. The spec of Miracast over Infrastructure (MICE) is available [here](https://winprotocoldoc.blob.core.windows.net/productionwindowsarchives/MS-MICE/%5bMS-MICE%5d.pdf). Compared to wifi p2p, it allows more stable connection and lower latency. Although MICE relies on Ethernet or secure wifi network almost entirely, in the device discovery phase, it still requires a wifi p2p device to broadcast beacon and probe response frames to the source. (However, it might be possible to use two Pis so that one of the two does not need to have wifi hardware or be physically close to the source. One Pi would be used to trasmit the beacon while the other (that runs ``./project.py``) is used to project. For such setting to work using the current script, however, the variable ``hostname`` in ``mice.py`` must set to the hostname of the machine running ``project.py``. In the future, it might be possible to emulate a wifi card by HW/SW on the source so that wifi p2p will not be necessary.)  

Currently, this feature is tested to be working with a Windows 10 PC and a Pi connected via Ethernet. More testings might be needed. Also, the encryption feature is not implemented yet so it should only be used over trusted networks and it should not be used for sensitive data.

This feature is not fully compatible with ``all.sh``. If ``all.sh`` has been running since booting, first run ``./removep2p`` before running the scripts. (It might be possible to run traditional method and MICE simultaneously if ``all.sh`` launches later than the script of MICE.)
## Preparation
Install NetworkManager, as described in the previous preparation section. It is required for MICE.   
Install avahi-utils:
```
sudo apt install avahi-utils
```
Make sure the Windows 10 PC is on the same network as the Pi. You can try pinging the Pi from the PC.  
## Usage
Make sure there is no p2p interface that has already been created. (If this is not the case, run ``./removep2p`` or simply reboot.)  
Run ``./mice.py``.  
Use the "Connect" tab in Windows 10 and try to connect to <the hostname of Pi> (e.g., raspberrypi). Windows may try to connect using the traditional method first and therefore may ask for PIN. In that case, simply cancel the connection process and try again. You can also try relaunching ``mice.py`` and see if it helps. Since no encryption is implemented at the moment, the prompt for PIN should not appear using MICE.  
Since some of the message exchanges have not been implemented, instead of its hostname, sometimes the Pi will appear as "Device" on the PC.

# Others
Some parts of the video player1 are modified from the codes on https://github.com/Apress/raspberry-pi-gpu-audio-video-prog. Many thanks to the author of "Raspberry Pi GPU Audio Video Programming" and, by extension, authors of omxplayer.  
Using any part of the codes in this project in commercial products is prohibited.
