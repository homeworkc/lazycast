#!/bin/bash

# sudo killall wpa_supplicant; sudo wpa_supplicant -Dnl80211 -iwlan0 -C/var/run/wpa_supplicant/ -c/etc/wpa_supplicant/wpa_supplicant.conf -dd

cd wpa_supplicant-2.9/wpa_supplicant
make
sudo killall wpa_supplicant
sudo ./wpa_supplicant -Dnl80211 -iwlan0 -C/var/run/wpa_supplicant/ -c/etc/wpa_supplicant/wpa_supplicant.conf -dd

make; sudo killall wpa_supplicant;sleep 3;sudo ./wpa_supplicant -dd -u -f  ~/log.txt  -B
sudo killall wpa_supplicant; make; sudo ./wpa_supplicant -dd -u -f  ~/log.txt  -B; python ~/p2p_group_add.py
