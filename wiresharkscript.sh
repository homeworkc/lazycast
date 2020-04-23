#!/bin/bash
sudo iw dev wlo1 interface add mon0 type monitor
sudo ip link set mon0 up
wireshark