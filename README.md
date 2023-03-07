lazycast: A Simple Wireless Display Receiver

# Description
lazycast is a simple wifi display receiver. It was originally targeted Raspberry Pi (as display) and Windows 8.1/10 (as source), but it **might** also work on other Linux platforms and Miracast sources. (For other Linux systems, skip the preparation section. For video playback from Android sources, modify the ``player_select`` option in ``d2.py``.) For Windows 10 systems, the Miracast over Infrastructure (**MICE**) feature is also supported, which may provide better user experiences. In general, lazycast does not require re-compilation of wpa_supplicant to support various p2p functionalities, and should work on an "out of the box" Raspberry Pi.

# Important Information
If you are using the latest Raspberry Pi OS ("Bullseye"),  follow [these instructions](https://github.com/homeworkc/lazycast/issues/100) and directly go to the [Build Binaries](https://github.com/homeworkc/lazycast/#build-binaries) section.



# Preparation
## Downgrade wpa_supplicant (only for Raspbian Buster)
**For Raspbian Buster, downgrade the ``wpasupplicant`` package to the version for Raspbian Stretch:**
```
wget http://ftp.us.debian.org/debian/pool/main/w/wpa/wpasupplicant_2.4-1+deb9u6_armhf.deb
sudo apt --allow-downgrades install ./wpasupplicant_2.4-1+deb9u6_armhf.deb
```  
## Install NetworkManager  (for Raspbian Buster or older)
**It is highly recommended to replace the "Wireless & Wired Network" in Raspbian with NetworkManager, which can maintain much more stable p2p connection.**  
**Note that installing NetworkManager will reset the network and cause Pi to be disconnected from existing network. Therefore, these steps should be done locally and not over SSH. After the installation, you can connect to the network once again using the NetworkManager interface.**  
Here is one solution (adopted from [here](https://raspberrypi.stackexchange.com/questions/29783/how-to-setup-network-manager-on-raspbian)):
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
## Build Binaries
Install packages (for compiling the players):
```
sudo apt install libx11-dev libasound2-dev libavformat-dev libavcodec-dev
```
Compile libraries on Pi:
```
cd /opt/vc/src/hello_pi/libs/ilclient/
sudo make
cd /opt/vc/src/hello_pi/hello_video
sudo make
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
Run `./all.sh` to initiate lazycast receiver. Wait until the "The display is ready" message. The name of the display will appear after this message. Then, search for this name on the source device you want to cast. The default PIN number is ``31415926``. If backchannel control is supported by the source, keyboard and mouse input on Pi are redirected to the source as remote controls.  

It is recommended to initiate the termination of the receiver on the source side. These user controls are often near the pairing controls on the source device. You can utilize the backchannel feature to remotely control the source device in order to close lazycast.  


# Tips
Set the resolution on the source side. lazycast advertises all possible resolutions regardless of the current rendering resolution. Therefore, you may want to change the resolution (on the source) to match the actual resolution of the display connecting to Pi.  

Modify parameters in the "settings" section in ``d2.py`` to change the sound output port (hdmi/3.5mm) and preferred player.  

The maximum resolutions supported are 1920x1080p60 and 1920x1200p30. The GPU on Pi may struggle to handle 1920x1080p60, which results in high latency. In this case, reduce the FPS to 1920x1080p50.  

To change the default PIN number, replace the string ``31415926`` in ``all.sh`` to another 8-digit number.  

You can hide Pi's cursor by using ``unclutter -idle 3``. See [this post](https://forums.raspberrypi.com/viewtopic.php?t=234879#p1437648).

After Pi connects to the source, it has an IP address of ``192.168.173.1`` and this connection can be reused for other purposes like SSH. On the other hand, since they are under the same subnet, precautions should be taken to prevent unauthorized access to Pi by anyone who knows the PIN number.    

Two in-house players are written for Raspberry Pi 3. VLC, omxplayer or gstreamer can be used instead on other platforms. (See [here](https://gstreamer.freedesktop.org/documentation/installing/on-linux.html) for details of installing gstreamer.) 

**It is very important that no background WiFi scanning occurs during casting. On Raspberry Pi, lazycast will automatically disable ``lxpanel`` during casting (in order to stop the ``lxplug-network`` plugin from scanning the network), and re-enable ``lxpanel`` after the casting is terminated. You can double-check that no background WiFi scanning happens by running ``iw event`` in a second terminal (and no event should be shown). [This post](https://forums.raspberrypi.com/viewtopic.php?t=250729#p1772473) has more information.**

# Known issues
lazycast tries to remember the pairing credentials so that entering the PIN is only needed once for each device. However, this feature does not seem to work properly all the time with recent Raspbian images. Therefore, re-pairing may be needed after every Raspberry Pi reboot. Try clearing the 'lazycast' information on the source device before re-pairing if you run into pairing problems.  

Player2 seems to have a double-free bug which causes it to crash when playing some videos. Currently a workaround (that constantly monitors the liveliness of player2) is implemented.

Latency: Limited by the implementation of the rtp player used. (In VLC, latency can be reduced from 1200 to 300ms by lowering the network cache value.)  

Due to the overcrowded nature of the wifi spectrum and the use of unreliable rtp transmission, you may experience some video glitching/audio stuttering. The in-house players employ several mechanisms to conceal transmission error, but it may still be noticeable in challenging wireless environments. Interference from other devices may cause disconnections.  

Devices may not fully support backchannel control and some keystrokes/clicks will behave differently in this case. The left Windows key is not captured and when it is pressed, it makes the current window to be out-of-focus and thus disables the backchannel controls. If it is pressed again the window will be in-focus. Also, keyboard backchannel and hiding the cursor do not seem to work properly on recent systems.

HDCP(content protection): Neither the key nor the hardware is available on Pi and therefore is not supported.  

<!-- Some Windows 10 devices seem to disconnect shortly after a connection is established. You can try using ``win10debug.sh`` instead of ``all.sh`` and see if it helps. -->

# Start on boot

Append this line to ``/etc/xdg/lxsession/LXDE-pi/autostart``:
```
@lxterminal -l --working-directory=<absolute path of lazycast> -e ./all.sh
```
For example, if lazycast is placed under ``~/`` (which is ``/home/pi/``, if your username is ``pi``), append the following line to the file:
```
@lxterminal -l --working-directory=/home/pi/lazycast -e ./all.sh
```

# Miracast over Infrastructure

**This feature was tested only on Raspbian Buster and a PC with an older version of Windows 10** 

For Windows 10 sources, Miracast over Infrastructure (MICE) is a feature that allows transmission of screen data over Ethernet or secure wifi networks. The spec of Miracast over Infrastructure (MICE) is available [here](https://winprotocoldoc.blob.core.windows.net/productionwindowsarchives/MS-MICE/%5bMS-MICE%5d.pdf). Compared to wifi p2p, it allows stabler connection and lower latency. Although MICE relies on Ethernet or secure wifi network almost entirely, in the device discovery phase, it still requires a wifi p2p device to broadcast beacon and probe response frames to the source. (However, it might be possible to use two Pis so that one of the two does not need to have wifi hardware or be physically close to the source. One Pi would be used to trasmit the beacon while the other (that runs ``./project.py``) is used to project. For such setting to work, the variable ``hostname`` in ``mice.py`` must be set to the hostname of the machine running ``project.py``. In the future, it might be possible to emulate a wifi card by HW/SW on the source so that wifi p2p will not be necessary.)  

Currently, this feature is tested to be working with a Windows 10 PC and a Pi (with manually assigned IPs) connected via Ethernet. More tests might be needed, especially for different DHCP, DNS and firewall configurations. Ports used include but are not limited to UDP 53 (DNS), UDP 5353 (mDNS), TCP 7236 and TCP 7250. Also, the encryption feature is not implemented yet so it should only be used over trusted networks and it should not be used for sensitive data. MICE works in ipv6 networks but currently only ipv4 is implemented.  

## Preparation
Follow the steps in the previous preparation section. Note that installing NetworkManager is required for MICE.   
Install avahi-utils:
```
sudo apt install avahi-utils
```
Make sure the Windows 10 PC is on the same network as the Pi. You can try pinging the Pi from the PC.  
## Usage
Make sure there is no p2p interface that has already been created and ``all.sh`` is not running. (You can disable ``all.sh`` to start on boot and then simply reboot.)  

Run ``./mice.py``.  

Use the "Connect" tab in Windows 10 and try to connect to the hostname of Pi (e.g., raspberrypi). Windows may try to connect using the traditional method first and therefore may ask for PIN. In that case, simply cancel the connecting process and try again. You can also try relaunching ``mice.py`` and see if it helps. Since no encryption is implemented at the moment, the prompt for PIN should not appear using MICE.  

Windows 10 assigns the name of the display differently when using MICE. If the monitor connected to the Pi is successfully detected by the PC, the name of the display (e.g., raspberrypi) will be changed to the name of the monitor. If the detection fails, the name of the display will be changed to "Device". After disconnection, the name of the display will be changed back to the hostname of Pi (e.g., raspberrypi).  

If you wish to run MICE and wifi p2p simultaneously, set the parameter ``concurrent`` to ``1`` in ``mice.py`` and only uses ``mice.py``. When there are multiple IPs assigned to the Pi and mDNS does not seem to be working, manually set the ``ipstr`` variable in ``mice.py`` to the target IP of Pi and a PC will try to connect to this IP directly.  
# Others
Some parts of the video player1 are modified from the codes on https://github.com/Apress/raspberry-pi-gpu-audio-video-prog. Many thanks to the author of "Raspberry Pi GPU Audio Video Programming" and, by extension, authors of omxplayer.  
Using any part of the codes in this project in commercial products is prohibited.
