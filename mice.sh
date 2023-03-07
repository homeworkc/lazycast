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
################################################################################
sudo systemctl stop dhcpcd
sudo systemctl stop wpa_supplicant
sudo wpa_supplicant -Dnl80211 -iwlan0 -u -c/etc/wpa_supplicant/wpa_supplicant.conf &

LD_LIBRARY_PATH=/opt/vc/lib
export LD_LIBRARY_PATH
./newmice.py