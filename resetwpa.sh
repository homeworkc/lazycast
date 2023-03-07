#!/bin/bash
sudo pkill wpa_supplicant
sudo systemctl restart dhcpcd
sudo systemctl restart wpa_supplicant
