#!/bin/bash

cwd=$(pwd)
HOSTNAME=raspberrypi
USERNAME=pi
PASSWORD=pi1234
PORT=22

while true; do
  sshpass -p "$PASSWORD" scp pi@raspberrypi:/home/pi/output.pcap $cwd/output.pcap
done
