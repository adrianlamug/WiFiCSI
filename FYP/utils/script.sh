#!/bin/bash

mcp -C 1 -N 1 -c 36/80
sudo ifconfig wlan0 up
nexutil -Iwlan0 -s500 -b -l34 -vKuABEQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==
sudo iw dev wlan0 interface add mon0 type monitor
sudo ip link set mon0 up
